import six
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import ckan.lib.helpers as helpers
import ckan.model as model
from ckanext.pages.db import MainPage,Page , News, Event, HeaderMainMenu, HeaderLogo, HeaderSecondaryMenu
from ckanext.pages.logic.schema import main_page_schema, update_pages_schema
import ckan.lib.navl.dictization_functions as df
from flask import request, flash
from ckan.types import Context
from ckan.common import current_user, _
from typing import Any, Optional, Union, cast
config = tk.config
_ = tk._


def _get_context():
    context = cast(Context, {
        u'model': model,
        u'session': model.Session,
        u'user': current_user.name,
        u'auth_user_obj': current_user,
    })
    return context


def _parse_form_data(request):
    return logic.clean_dict(
        dict_fns.unflatten(
            logic.tuplize_dict(
                logic.parse_params(request.form)
            )
        )
    )


class HeaderLogoUtils:
    @classmethod
    def get_all(cls):
        return HeaderLogo.get_all()

    @classmethod
    def create(cls, data):
        logo = HeaderLogo(**data)
        logo.save()
        return logo

    @classmethod
    def update(cls, logo_id, data):
        logo = HeaderLogo.get(logo_id)
        for key, value in data.items():
            setattr(logo, key, value)
        logo.save()
        return logo

    @classmethod
    def delete(cls, logo_id):
        logo = HeaderLogo.get(logo_id)
        if logo:
            logo.delete()
        return logo

    @classmethod
    def toggle_visibility(cls, logo_id):
        logo = HeaderLogo.get(logo_id)
        if logo:
            logo.is_visible = not logo.is_visible
            logo.save()
        return logo

class HeaderMainMenuUtils:
    @classmethod
    def get_all(cls):
        return HeaderMainMenu.get_all()

    @classmethod
    def get_top_level(cls):
        return HeaderMainMenu.get_top_level()

    @classmethod
    def create(cls, data):
        menu = HeaderMainMenu(**data)
        menu.save()
        return menu

    @classmethod
    def update(cls, menu_id, data):
        menu = HeaderMainMenu.get(menu_id)
        for key, value in data.items():
            setattr(menu, key, value)
        menu.save()
        return menu

    @classmethod
    def delete(cls, menu_id):
        menu = HeaderMainMenu.get(menu_id)
        if menu:
            menu.delete()
        return menu

    @classmethod
    def toggle_visibility(cls, menu_id):
        menu = HeaderMainMenu.get(menu_id)
        if menu:
            menu.is_visible = not menu.is_visible
            menu.save()
        return menu

class HeaderSecondaryMenuUtils:
    @classmethod
    def get_all(cls):
        return HeaderSecondaryMenu.get_all()

    @classmethod
    def create(cls, data):
        menu = HeaderSecondaryMenu(**data)
        menu.save()
        return menu

    @classmethod
    def update(cls, menu_id, data):
        menu = HeaderSecondaryMenu.get(menu_id)
        for key, value in data.items():
            setattr(menu, key, value)
        menu.save()
        return menu

    @classmethod
    def delete(cls, menu_id):
        menu = HeaderSecondaryMenu.get(menu_id)
        if menu:
            menu.delete()
        return menu

    @classmethod
    def toggle_visibility(cls, menu_id):
        menu = HeaderSecondaryMenu.get(menu_id)
        if menu:
            menu.is_visible = not menu.is_visible
            menu.save()
        return menu

class Form:
    # Input field method
    def input(self, name, **kwargs):
        value = kwargs.get('value', '')
        label = kwargs.get('label', '')
        error = kwargs.get('error', '')
        css_class = ' '.join(kwargs.get('classes', []))
        return f'''
            <div class="mb-3">
                <label for="{name}" class="form-label">{label}</label>
                <input type="text" id="{name}" name="{name}" value="{value}" class="{css_class}">
                <div class="text-danger">{error}</div>
            </div>
        '''

    # Checkbox method
    def checkbox(self, name, **kwargs):
        checked = 'checked' if kwargs.get('checked') else ''
        label = kwargs.get('label', '')
        error = kwargs.get('error', '')
        return f'''
            <div class="mb-3 form-check">
                <input type="checkbox" id="{name}" name="{name}" {checked} class="form-check-input">
                <label for="{name}" class="form-check-label">{label}</label>
                <div class="text-danger">{error}</div>
            </div>
        '''

    # Textarea method
    def textarea(self, name, **kwargs):
        value = kwargs.get('value', '')
        label = kwargs.get('label', '')
        error = kwargs.get('error', '')
        css_class = ' '.join(kwargs.get('classes', []))
        return f'''
            <div class="mb-3">
                <label for="{name}" class="form-label">{label}</label>
                <textarea id="{name}" name="{name}" class="{css_class}">{value}</textarea>
                <div class="text-danger">{error}</div>
            </div>
        '''




def validate_page_data(data):

    schema = update_pages_schema()
    return df.validate(data, schema)

def news_edit(page=None, data=None, errors=None, error_summary=None):
    if request.method == 'POST':
        form_data = _parse_form_data(request)
        try:
            # Generate a slug for the 'name' field if it's missing
            if not form_data.get('name'):
                form_data['name'] = form_data.get('title_en', '').strip().lower().replace(' ', '-')[:50]

            # Check if this is an update or a new entry
            news_id = form_data.get('id')  # Retrieve the id from the form data
            if news_id:
                # Update the existing news
                existing_news = model.Session.query(News).get(news_id)
                if not existing_news:
                    raise tk.ObjectNotFound(_("News not found"))
                for key, value in form_data.items():
                    setattr(existing_news, key, value)
                model.Session.commit()
            else:
                # Create a new news entry
                new_news = News(**form_data)
                model.Session.add(new_news)
                model.Session.commit()
                news_id = new_news.id  # Retrieve the newly created ID

            # Redirect back to the news edit page
            return tk.redirect_to('pages.news_index')
        except tk.ValidationError as e:
            model.Session.rollback()
            return tk.render(
                'ckanext_pages/news_edit.html',
                extra_vars={
                    'data': form_data,
                    'errors': e.error_dict,
                    'error_summary': e.error_summary,
                },
            )
    else:
        news_data = model.Session.query(News).get(page) if page else News()

        if news_data.content_en is None:
            news_data.content_en = ""
        if news_data.content_ar is None:
            news_data.content_ar = ""

        return tk.render(
            'ckanext_pages/news_edit.html',
            extra_vars={
                'data': news_data,
                'errors': errors or {},
                'error_summary': error_summary or {},
            },
        )




 


def _inject_views_into_page(_page):
    if not p.plugin_loaded('image_view'):
        return
    try:
        import lxml
        import lxml.html
    except ImportError:
        return

    try:
        root = lxml.html.fromstring(_page['content'])
    except (lxml.etree.XMLSyntaxError,
            lxml.etree.ParserError):
        return

    for element in root.findall('.//iframe'):
        embed_element = element.attrib.pop('data-ckan-view-embed', None)
        if not embed_element:
            continue
        element.tag = 'div'
        error = None

        try:
            iframe_src = element.attrib.pop('src', '')
            width = element.attrib.pop('width', '80')
            if not width.endswith('%') and not width.endswith('px'):
                width = width + 'px'
            height = element.attrib.pop('height', '80')
            if not height.endswith('%') and not height.endswith('px'):
                height = height + 'px'
            align = element.attrib.pop('align', 'none')
            style = "width: %s; height: %s; float: %s; overflow: auto; vertical-align:middle; position:relative" \
                    % (width, height, align)
            element.attrib['style'] = style
            element.attrib['class'] = 'pages-embed'
            view = tk.get_action('resource_view_show')({}, {'id': iframe_src[-36:]})
            context = {}
            resource = tk.get_action('resource_show')(context, {'id': view['resource_id']})
            package_id = context['resource'].resource_group.package_id
            package = tk.get_action('package_show')(context, {'id': package_id})
        except tk.ObjectNotFound:
            error = _('ERROR: View not found {view_id}'.format(view_id=iframe_src))

        if error:
            resource_view_html = '<h4> %s </h4>' % error
        elif not helpers.resource_view_is_iframed(view):
            resource_view_html = helpers.rendered_resource_view(view, resource, package)
        else:
            src = helpers.url_for(
                'resource.view', id=package['name'], resource_id=resource['id'],
                view_id=view['id'], _external=True
            )
            message = _('Your browser does not support iframes.')
            resource_view_html = '<iframe src="{src}" frameborder="0" width="100%" height="100%" ' \
                                 'style="display:block"> <p>{message}</p> </iframe>'.format(src=src, message=message)

        view_element = lxml.html.fromstring(resource_view_html)
        element.append(view_element)

    new_content = six.ensure_text(lxml.html.tostring(root))
    if new_content.startswith('<div>') and new_content.endswith('</div>'):

        new_content = new_content[5:-6]
    elif new_content.startswith('<p>') and new_content.endswith('</p>'):

        new_content = new_content[3:-4]
    _page['content'] = new_content



def pages_upload():
    if not tk.request.method == 'POST':
        tk.abort(409, _('Only Posting is availiable'))
    data_dict = logic.clean_dict(
        dict_fns.unflatten(
            logic.tuplize_dict(
                logic.parse_params(tk.request.files)
            )
        )
    )
    try:
        upload_info = tk.get_action('ckanext_pages_upload')(_get_context(), data_dict)
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to upload file %s') % id)

    return upload_info








def _has_user_role_for_some_org(user: model.User, role):
    q = model.Session.query(model.Member)\
        .filter(model.Member.table_id == user.id)\
        .filter(model.Member.state == 'active')\
        .filter(model.Member.capacity.in_(['admin'] + [role]))

    return bool(q.count())

def is_data_coordinator(context):
    user = context.get('user')
    model = context['model']
    user_obj = model.User.get(user)

    return _has_user_role_for_some_org(user_obj, 'member')


def get_main_page(section_id):
    return MainPage.get(id=section_id)

def validate_main_page(section_id, data):
    schema = main_page_schema(id=section_id)
    try:
        errors = p.toolkit.navl_validate(data, schema)
        if errors:
            print("Validation Errors:", errors)  # Debugging
            return False, errors
        return True, None
    except Exception as e:
        print("Validation Exception:", str(e))  # Debugging
        return False, {'error': str(e)}


def update_main_page(section_id, data):
    section = get_main_page(section_id)
    if section:
        section.main_title_1_ar = data.get('main_title_1_ar')
        section.main_title_1_en = data.get('main_title_1_en')
        section.main_title_2_ar = data.get('main_title_2_ar')
        section.main_title_2_en = data.get('main_title_2_en')
        section.main_brief_en = data.get('main_brief_en')
        section.main_brief_ar = data.get('main_brief_ar')
        model.Session.commit()
        return {"success": True}
    return {"success": False, "error": "Section not found"}


def main_page_edit(section_id):
    context = _get_context()
    section_titles = {
        1: "Main Title & Brief",
        2: "Open Data Sector",
        3: "Indicators",
        4: "Open Data In Numbers",
        5: "Also Explore"
    }

    try:

        if tk.request.method == 'POST':
            data_dict = dict(tk.request.form)
            data_dict['id'] = section_id

            if tk.request.form.get('back'):
                return tk.redirect_to('pages.main_page')

            try:
                tk.get_action('ckanext_main_page_edit')(
                    context, data_dict
                )
                tk.h.flash_success(tk._('Section updated successfully!'))
                return tk.redirect_to('pages.main_page')
            except tk.ValidationError as e:
                errors = e.error_dict if hasattr(e, 'error_dict') else e
                error_summary = e.error_summary if hasattr(e, 'error_summary') else {
                    field: tk._('Invalid value') for field in errors.keys()
                }
                return tk.render(
                    'main_page/main_page_edit.html',
                    extra_vars={
                        'has_two_titles': True if int(section_id) == 1 else False,
                        'section_title': section_titles.get(int(section_id), "Unknown Section"),
                        'data': data_dict,
                        'errors': errors,
                        'error_summary': error_summary
                    }
                )

        main_page_dict = tk.get_action('ckanext_main_page_show')(
            context, {'section_id': section_id}
        )
        if main_page_dict is None:
            raise tk.ObjectNotFound('Section not found')

        return tk.render(
            'main_page/main_page_edit.html',
            extra_vars={
                'has_two_titles': True if int(section_id) == 1 else False,
                'section_title': section_titles.get(int(section_id), "Unknown Section"),
                'data': main_page_dict,
                'errors': {},
                'error_summary': None
            }
        )

    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to edit main page sections'))
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Section not found'))


def main_page():
    sections = MainPage.all()

    section_titles = {
        1: "Title & Brief",
        2: "Open Data Sector",
        3: "Indicators",
        4: "Open Data In Numbers",
        5: "Also Explore"
    }
    data = []
    for section in sections:
        data.append({
            'id': section.id,
            'name': f"Section {section.id}: {section_titles.get(section.id)}",
            'last_update': "25/09/2024"
        })

    return tk.render('main_page/main_page.html', extra_vars={'sections': data})
