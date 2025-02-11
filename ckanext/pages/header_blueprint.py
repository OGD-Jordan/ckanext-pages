from ckan import model
from flask import Blueprint
from ckan.plugins import toolkit as tk
import ckan.lib.helpers as h
from ckan.types import Context
from ckan.common import current_user, _
from typing import  cast

header_management = Blueprint('header_management', __name__, url_prefix='/cms/header')


def _get_context():
    context = cast(Context, {
        u'model': model,
        u'session': model.Session,
        u'user': current_user.name,
        u'auth_user_obj': current_user,
    })
    return context


@header_management.route('/', methods=['GET'])
def index():
    context = _get_context()

    try:
        tk.check_access('ckanext_header_management_access', context)

        menu_type = tk.request.args.get('menu_type')

        main_menu = tk.get_action('ckanext_header_main_menu_list')(
            context, {'menu_type': menu_type}
        )
        secondary_menu = tk.get_action('ckanext_header_secondary_menu_list')(
            context, {}
        )
        logo = tk.get_action('ckanext_header_logo_get')(context, {})

        extra_vars = {
            'main_menu': main_menu,
            'secondary_menu': secondary_menu,
            'logo': logo,
            'menu_type': menu_type
        }

        return tk.render('ckanext_pages/header_management/index.html', extra_vars)
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to manage headers'))


@header_management.route('/main-menu/toggle-visibility/<id>', methods=['GET'])
def toggle_main_menu_visibility(id):
    context = _get_context()

    try:
        tk.get_action('ckanext_header_main_menu_toggle_visibility')(
            context, {'id': id}
        )

        h.flash_success(tk._('Menu item visibility updated'))
    except tk.NotAuthorized:
        h.flash_error(tk._('Not authorized to update menu items'))
    except tk.ObjectNotFound:
        h.flash_error(tk._('Menu item not found'))

    return h.redirect_to('header_management.index')


@header_management.route('/main-menu/delete/<id>', methods=['POST'])
def delete_main_menu(id):
    context = _get_context()

    try:
        tk.get_action('ckanext_header_main_menu_delete')(
            context, {'id': id}
        )
        h.flash_success(tk._('Menu item deleted'))
    except tk.NotAuthorized:
        h.flash_error(tk._('Not authorized to delete menu items'))
    except tk.ObjectNotFound:
        h.flash_error(tk._('Menu item not found'))
    except tk.ValidationError as e:
        h.flash_error(e.error_dict['id'])

    return h.redirect_to('header_management.index')


@header_management.route('/secondary-menu/toggle-visibility/<id>', methods=['GET'])
def toggle_secondary_menu_visibility(id):
    context = _get_context()

    try:
        tk.get_action('ckanext_header_secondary_menu_toggle_visibility')(
            context, {'id': id}
        )
        h.flash_success(tk._('Menu item visibility updated'))
    except tk.NotAuthorized:
        h.flash_error(tk._('Not authorized to update menu items'))
    except tk.ObjectNotFound:
        h.flash_error(tk._('Menu item not found'))

    return h.redirect_to('header_management.index')


@header_management.route('/logo/delete/<id>', methods=['POST'])
def delete_logo(id):
    context = _get_context()

    try:
        tk.get_action('ckanext_header_logo_delete')(
            context, {'id': id}
        )
        h.flash_success(tk._('Header logo deleted'))
    except tk.NotAuthorized:
        h.flash_error(tk._('Not authorized to delete logo'))
    except tk.ObjectNotFound:
        h.flash_error(tk._('Menu item not found'))

    return h.redirect_to('header_management.index')


@header_management.route('/logo/toggle-visibility/<id>', methods=['GET'])
def toggle_logo_visibility(id):
    context = _get_context()

    try:
        tk.get_action('ckanext_header_logo_toggle_visibility')(
            context, {'id': id}
        )
        h.flash_success(tk._('Header logo visibility updated'))
    except tk.NotAuthorized:
        h.flash_error(tk._('Not authorized to update logo'))
    except tk.ObjectNotFound:
        h.flash_error(tk._('Logo not found'))

    return h.redirect_to('header_management.index')


@header_management.route('/logo/edit/<id>', methods=['GET', 'POST'])
def edit_logo(id):
    context = {
        'user': tk.g.user,
        'auth_user_obj': tk.g.userobj
    }

    try:
        tk.check_access('ckanext_header_management_access', context)

        if tk.request.method == 'POST':
            data_dict = {
                'id': id,
                '__extras': {}
            }

            # Handle file uploads
            upload_ar = tk.request.files.get('logo_ar')
            upload_en = tk.request.files.get('logo_en')

            if upload_ar:
                data_dict['logo_ar_upload'] = upload_ar
                data_dict['clear_logo_ar'] = False

            if upload_en:
                data_dict['logo_en_upload'] = upload_en
                data_dict['clear_logo_en'] = False

            try:
                tk.get_action('ckanext_header_logo_update')(context, data_dict)

                if upload_ar or upload_en:
                    tk.h.flash_success(tk._('Header logo uploaded successfully'))

                return tk.h.redirect_to('header_management.index')

            except tk.ValidationError as e:
                tk.h.flash_error(e.error_summary)
                return tk.render(
                    'ckanext_pages/header_management/edit_header_logo.html',
                    extra_vars={
                        'data': data_dict,
                        'errors': e.error_dict,
                        'error_summary': e.error_summary
                    }
                )

        logo = tk.get_action('ckanext_header_logo_get')(context, {'id': id})
        return tk.render(
            'ckanext_pages/header_management/edit_header_logo.html',
            extra_vars={
                'data': logo,
                'errors': {},
                'error_summary': {}
            }
        )

    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to edit logo'))
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Logo not found'))

@header_management.route('/main-menu/new', methods=['GET', 'POST'])
def new_main_menu():
    context = _get_context()

    try:
        tk.check_access('ckanext_header_management_access', context)
        parent_menus = tk.get_action('ckanext_header_main_menu_parent_list')(context, {})

        if tk.request.method == 'POST':
            data_dict = dict(tk.request.form)
            data_dict.update(tk.request.files.to_dict())

            # Check number of root items if no parent selected
            if not data_dict.get('parent_id'):
                if len(parent_menus) >= 6:
                    h.flash_error(
                        tk._('Not More Than 6 Items Can Be Added to Main Header Without Any Parent.')
                    )
                    return tk.render(
                        'ckanext_pages/header_management/edit_main_menu.html',
                        extra_vars={
                            'parent_menus': parent_menus,
                            'data': data_dict,
                            'errors': {'no_parent': True},
                            'error_summary': tk._('Maximum root items reached')
                        }
                    )

            try:
                tk.get_action('ckanext_header_main_menu_create')(context, data_dict)
                h.flash_success(tk._('Menu item created successfully'))
                return h.redirect_to('header_management.index')
            except tk.ValidationError as e:
                return tk.render(
                    'ckanext_pages/header_management/edit_main_menu.html',
                    extra_vars={
                        'parent_menus': parent_menus,
                        'data': data_dict,
                        'errors': e.error_dict,
                        'error_summary': e.error_summary
                    }
                )

        return tk.render(
            'ckanext_pages/header_management/edit_main_menu.html',
            extra_vars={
                'parent_menus': parent_menus,
                'data': {},
                'errors': {},
                'error_summary': {}
            }
        )

    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to create menu items'))


@header_management.route('/main-menu/edit/<id>', methods=['GET', 'POST'])
def edit_main_menu(id):
    context = _get_context()

    try:
        tk.check_access('ckanext_header_management_access', context)
        parent_menus = tk.get_action('ckanext_header_main_menu_parent_list')(context, {})

        if tk.request.method == 'POST':
            data_dict = dict(tk.request.form)
            data_dict['id'] = id

            # Check number of root items if no parent selected
            if not data_dict.get('parent_id'):
                if len(parent_menus) >= 6:
                    return tk.render(
                        'ckanext_pages/header_management/edit_main_menu.html',
                        extra_vars={
                            'parent_menus': parent_menus,
                            'data': data_dict,
                            'errors': {'no_parent': True},
                            'error_summary': {
                                "parent": tk._('Not More Than 6 Items Can Be Added to Main Header Without Any Parent.')
                            }
                        }
                    )

            try:
                tk.get_action('ckanext_header_main_menu_edit')(
                    context, data_dict
                )
                h.flash_success(tk._('Menu item updated'))
                return h.redirect_to('header_management.index')
            except tk.ValidationError as e:
                return tk.render(
                    'ckanext_pages/header_management/edit_main_menu.html',
                    extra_vars={
                        'parent_menus': parent_menus,
                        'data': data_dict,
                        'errors': e.error_dict,
                        'error_summary': e.error_summary
                    }
                )

        menu_item = tk.get_action('ckanext_header_main_menu_show')(
            context, {'id': id}
        )
        return tk.render(
            'ckanext_pages/header_management/edit_main_menu.html',
            extra_vars={
                'parent_menus': parent_menus,
                'data': menu_item,
                'errors': {},
                'error_summary': None
            }
        )

    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to edit menu items'))
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Menu item not found'))


@header_management.route('/menu-item/details/<id>', methods=['GET'])
def menu_item_details(id):
    context = _get_context()

    try:
        tk.check_access('ckanext_header_management_access', context)

        menu_item = tk.get_action('ckanext_header_main_menu_show')(context, {'id': id})
        return tk.render('ckanext_pages/header_management/menu_item_details.html', extra_vars={'menu_item': menu_item})

    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to view menu item details'))
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Menu item not found'))


@header_management.route('/secondary-menu/new', methods=['GET', 'POST'])
def new_secondary_menu():
    context = _get_context()
    parent_menus = tk.get_action('ckanext_header_secondary_menu_parent_list')(context, {})
    try:
        tk.check_access('ckanext_header_management_access', context)

        if tk.request.method == 'POST':
            data_dict = dict(tk.request.form)
            data_dict.update(tk.request.files.to_dict())

            try:
                tk.get_action('ckanext_header_secondary_menu_create')(context, data_dict)
                h.flash_success(tk._('Menu item created successfully'))
                return h.redirect_to('header_management.index')
            except tk.ValidationError as e:
                return tk.render(
                    'ckanext_pages/header_management/edit_secondary_menu.html',
                    extra_vars={
                        'parent_menus': parent_menus,
                        'data': data_dict,
                        'errors': e.error_dict,
                        'error_summary': e.error_summary
                    }
                )

        return tk.render(
            'ckanext_pages/header_management/edit_secondary_menu.html',
            extra_vars={
                'parent_menus': parent_menus,
                'data': {},
                'errors': {},
                'error_summary': {}
            }
        )

    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to create menu items'))



@header_management.route('/secondary-menu/edit/<id>', methods=['GET', 'POST'])
def edit_secondary_menu(id):
    context = _get_context()
    parent_menus = tk.get_action('ckanext_header_secondary_menu_parent_list')(context, {})
    try:
        tk.check_access('ckanext_header_management_access', context)

        if tk.request.method == 'POST':
            data_dict = dict(tk.request.form)
            data_dict['id'] = id

            try:
                tk.get_action('ckanext_header_secondary_menu_edit')(context, data_dict)
                h.flash_success(tk._('Menu item updated'))
                return h.redirect_to('header_management.index')
            except tk.ValidationError as e:
                return tk.render(
                    'ckanext_pages/header_management/edit_secondary_menu.html',
                    extra_vars={
                        'parent_menus': parent_menus,
                        'data': data_dict,
                        'errors': e.error_dict,
                        'error_summary': e.error_summary
                    }
                )

        menu_item = tk.get_action('ckanext_header_secondary_menu_show')(context, {'id': id})
        return tk.render(
            'ckanext_pages/header_management/edit_secondary_menu.html',
            extra_vars={
                'parent_menus': parent_menus,
                'data': menu_item,
                'errors': {},
                'error_summary': {}
            }
        )

    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to edit menu items'))
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Menu item not found'))


@header_management.route('/secondary-menu/delete/<id>', methods=['POST'])
def delete_secondary_menu(id):
    context = _get_context()

    try:
        tk.get_action('ckanext_header_secondary_menu_delete')(
            context, {'id': id}
        )
        h.flash_success(tk._('Menu item deleted'))
    except tk.NotAuthorized:
        h.flash_error(tk._('Not authorized to delete menu items'))
    except tk.ObjectNotFound:
        h.flash_error(tk._('Menu item not found'))
    except tk.ValidationError as e:
        h.flash_error(e.error_dict['id'])

    return h.redirect_to('header_management.index')




# blueprints

def get_blueprints():
    return [header_management]
