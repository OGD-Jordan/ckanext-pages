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




import ckan.lib.base as base
from flask.views import MethodView
from typing import Union, cast
from ckan.types import Context, Response
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
from flask import Blueprint, request
from ckan.views.home import CACHE_PARAMETERS

_clean_dict = logic.clean_dict
_tuplize_dict = logic.tuplize_dict
_parse_params = logic.parse_params


class Column1Edit(MethodView):
    def _prepare(self) -> Context:
        context = cast(Context, {
            u'model': model,
            u'session': model.Session,
            u'user': current_user.name,
            u'auth_user_obj': current_user,
        })

        try:
            tk.check_access(u'is_content_editor', context)
        except tk.NotAuthorized:
            return base.abort(403, _(u'Unauthorized to update CMS footer'))
        return context


    def post(self, id) -> Union[Response, str]:
        context = self._prepare()

        data_dict = _clean_dict(
            dict_fns.unflatten(
                _tuplize_dict(_parse_params(tk.request.form))))

        data_dict.update(
            _clean_dict(dict_fns.unflatten(
                    _tuplize_dict(_parse_params(tk.request.files))
                    )))

        try:
            logos_data = tk.get_action('ckanext_header_logo_update')(context, data_dict)

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)

        url = 'header_management.index'
        return h.redirect_to(url)


    def get(self, id, data=None, errors=None, error_summary=None) -> str:

        context = self._prepare()
        
        data = data or _clean_dict(
            dict_fns.unflatten(
                _tuplize_dict(
                    _parse_params(request.args, ignore_keys=CACHE_PARAMETERS)
                )
            )
        )

        previous_logos_data = tk.get_action('ckanext_header_logo_get')(context, {})

        data = {**previous_logos_data, **data}


        errors = errors or {}
        error_summary = error_summary or {}

        errors_json = h.dump_json(errors)

        return base.render(
            'ckanext_pages/header_management/edit_header_logo.html', 
            extra_vars={
                u'errors_json': errors_json,
                u'data': data,
                u'errors': errors,
                u'error_summary': error_summary,
            }
        )
    
header_management.add_url_rule('/logo/edit/<id>', view_func=Column1Edit.as_view('edit_logo'), endpoint='edit_logo')


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
                            'error_summary': {
                                "parent": tk._('Not More Than 6 Items Can Be Added to Main Header Without Any Parent.')
                            }
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
                tk.get_action('ckanext_header_secondary_menu_create')(context, {**data_dict, 'menu_type': 'link'})
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
                tk.get_action('ckanext_header_secondary_menu_edit')(context, {**data_dict, 'menu_type': 'link'})
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
