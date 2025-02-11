import datetime
import json
import logging
from html.parser import HTMLParser

import ckan.lib.navl.dictization_functions as df
import ckan.lib.uploader as uploader
import ckan.plugins as p
from ckan import model
from ckan.plugins import toolkit as tk
from ckan.plugins.toolkit import _, h
from ckanext.comments.model.dictize import get_dictizer
from ckanext.pages import db
from ckanext.pages.db import MainPage, Page, Event, News, HeaderMainMenu, HeaderLogo, HeaderSecondaryMenu
from ckanext.pages.logic.schema import main_page_schema, header_logo_upload_schema
from ckanext.pages.logic.schema import (
    default_news_schema,
    update_events_schema,
    update_pages_schema,
    update_news_schema
)
from ckan.logic import validate as validate_decorator

from .logic.schema import default_pages_schema, header_menu_schema

log = logging.getLogger(__name__)

class HTMLFirstImage(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.first_image = None

    def handle_starttag(self, tag, attrs):
        if tag == 'img' and not self.first_image:
            self.first_image = dict(attrs)['src']

_ = tk._
_actions = {}


def action(func):
    func.__name__ = f"pages_{func.__name__}"
    _actions[func.__name__] = func
    return func


def get_actions():
    return _actions.copy()



def news_toggle_visibility(context, data_dict):
    tk.check_access("ckanext_news_toggle_visibility", context)
    news_id = data_dict.get('id')

    if not news_id:
        raise p.toolkit.ValidationError(_("Missing 'id' in request."))

    news = News.get(news_id)
    
    if not news:
        raise p.toolkit.ObjectNotFound(f"News with ID {news_id} not found.")

    news.hidden = not news.hidden
    News.Session.commit()

    return {'success': True, 'hidden': news.hidden}



@validate_decorator(update_events_schema)
def event_edit(context , data_dict):
    p.toolkit.check_access('ckanext_event_edit', context, data_dict)

    page_id = data_dict.get('id')
    page = Event.get(page_id) if page_id else Event()

    data_dict = single_image_upload(context, data_dict)

    # Update attributes
    for key, value in data_dict.items():
        if hasattr(Event, key):
            setattr(page, key, value)


    # Save and commit
    if not page_id:
        model.Session.add(page)
    page.modified = datetime.datetime.utcnow()
    model.Session.commit()

    # Return success with ID
    return {"success": True, "id": page.name}



@validate_decorator(update_news_schema)
def news_edit(context , data_dict):
    p.toolkit.check_access('ckanext_news_edit', context)

    page_id = data_dict.get('id')
    page = News.get(page_id) if page_id else News()

    data_dict = single_image_upload(context, data_dict)

    print('data_dict1',data_dict)
    for key, value in data_dict.items():
        if hasattr(News, key):
            setattr(page, key, value)

    print('page.image_url',page.image_url)
    if not page_id:
        page.add()
    page.modified = datetime.datetime.utcnow()
    page.commit()

    return tk.get_action('ckanext_news_show')(context, {'id': page.name})



@validate_decorator(default_pages_schema)
def pages_edit_action(context, data_dict):
    p.toolkit.check_access('ckanext_pages_edit', context)

    data_dict = single_image_upload(context, data_dict)

    # Fetch or create Page object
    page_id = data_dict.get('id')
    page = Page.get(page_id) if page_id else Page()

    if not page:
        raise tk.ObjectNotFound(_('Page not found.')) 

    # Update attributes
    for key, value in data_dict.items():
        if hasattr(Page, key):
            setattr(page, key, value)

    page.modified = datetime.datetime.utcnow()
    page.private = False
    if not page_id:
        model.Session.add(page)
    model.Session.commit()

    return tk.get_action('ckanext_pages_show')(context, {'id': page.id} )



def pages_upload(context, data_dict):
    """ Upload a file to the CKAN server.

    This method implements the logic for file uploads used by CKEditor. For
    more details on implementation and expected return values see:
     - https://ckeditor.com/docs/ckeditor4/latest/guide/dev_file_upload.html#server-side-configuration

    """

    try:
        p.toolkit.check_access('ckanext_pages_upload', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))

    upload = uploader.get_uploader('page_images')

    upload.update_data_dict(data_dict, 'image_url',
                            'image_upload', 'clear_upload')

    max_image_size = uploader.get_max_image_size()

    try:
        upload.upload(max_image_size)
    except p.toolkit.ValidationError:
        message = (
            "Can't upload the file, size is too large. "
            "(Max allowed is {0}mb)".format(max_image_size)
        )
        return {'uploaded': 0, 'error': {'message': message}}

    image_url = data_dict.get('image_url')
    if image_url and image_url[0:6] not in {'http:/', 'https:'}:
        image_url = h.url_for_static(
            'uploads/page_images/{}'.format(image_url),
            qualified=True
        )
    return {'url': image_url, 'fileName': upload.filename, 'uploaded': 1}


@tk.side_effect_free
def pages_show(context, data_dict):
    tk.check_access('ckanext_pages_show', context, data_dict)
    id = data_dict.get('id')
    out = db.Page.get(id)
    if out:
        image_url = out.image_url
        out = db.table_dictize(out, context)
        out.update({
            'display_image_url': h.url_for_static(
                'uploads/pages/{}'.format(image_url),
                qualified=True
                ) if out and image_url and image_url[0:6] not in {'http:/', 'https:'}  else image_url,
            })
    else:
        raise tk.ObjectNotFound(_('Page not found.')) 
    return out



@tk.side_effect_free
def pages_list(context, data_dict):
    p.toolkit.check_access('ckanext_pages_list', context, data_dict)
    query = model.Session.query(Page)

    sort = data_dict.get('sort', 'title_en asc')  # Default sorting
    sort_field = sort.split(' ')[0]
    sort_order = sort.split(' ')[1]
    if sort_field:
        if hasattr(Page, sort_field):
            if sort_order == 'desc':
                query = query.order_by(getattr(Page, sort_field).desc())
            else:
                query = query.order_by(getattr(Page, sort_field).asc())

    pages = query.all()

    out_list = []
    for pg in pages:
        image_url = pg.image_url
        out_list.append(db.table_dictize(pg, context))
        out_list[-1].update({
            'display_image_url': h.url_for_static(
                'uploads/pages/{}'.format(image_url),
                qualified=True
                ) if pg and image_url and image_url[0:6] not in {'http:/', 'https:'}  else image_url,
            })

    return out_list



@tk.side_effect_free
def news_list(context, data_dict):
    p.toolkit.check_access('ckanext_news_list', context)
    query = model.Session.query(News)

    sort = data_dict.get('sort', 'title_en asc')  # Default sorting
    sort_field = sort.split(' ')[0]
    sort_order = sort.split(' ')[1]
    if sort_field:
        if hasattr(News, sort_field):
            if sort_order == 'desc':
                query = query.order_by(getattr(News, sort_field).desc())
            else:
                query = query.order_by(getattr(News, sort_field).asc())

    news = query.all()
    time_now = datetime.datetime.now()

    out_list = []
    for pg in news:
        status = _("Disabled")
        if not pg.hidden:
            status = _("Upcoming") if pg.news_date > time_now else _("Posted")
        image_url = pg.image_url
        out_list.append(db.table_dictize(pg, context))
        out_list[-1].update({
            'status': status,
            'display_image_url': h.url_for_static(
                'uploads/pages/{}'.format(image_url),
                qualified=True
                ) if pg and image_url and image_url[0:6] not in {'http:/', 'https:'}  else image_url,
            })
        
    return out_list
    


@tk.side_effect_free
def events_list(context, data_dict):
    p.toolkit.check_access('ckanext_events_list', context, data_dict)
    query = model.Session.query(Event)

    sort = data_dict.get('sort', 'title_en asc')  # Default sorting
    sort_field = sort.split(' ')[0]
    sort_order = sort.split(' ')[1]
    if sort_field:
        if hasattr(Event, sort_field):
            if sort_order == 'desc':
                query = query.order_by(getattr(Event, sort_field).desc())
            else:
                query = query.order_by(getattr(Event, sort_field).asc())

    events = query.all()


    out_list = []
    today = datetime.datetime.now()
    
    for pg in events:
        image_url = pg.image_url
        status = _("Past Event")
        if pg.start_date <= today and pg.end_date > today:
            status = _("Currently Happening")
        elif pg.start_date > today:
            status = _("Upcoming")

        out_list.append(db.table_dictize(pg, context))
        out_list[-1].update({
            'status': status,
            'display_image_url': h.url_for_static(
                'uploads/pages/{}'.format(image_url),
                qualified=True
                ) if pg and image_url and image_url[0:6] not in {'http:/', 'https:'}  else image_url,
            })

    return out_list
    
def events_show(context, data_dict):
    tk.check_access('ckanext_event_show', context, data_dict)

    event_id = data_dict.get('id')

    if not event_id:
        raise tk.ValidationError({'id': 'Missing value'})

    today = datetime.datetime.now()

    event = Event.get(event_id)
    if event:
        status = _("Past Event")
        if event.start_date <= today and event.end_date > today:
            status = _("Currently Happening")
        elif event.start_date > today:
            status = _("Upcoming")
        image_url = event.image_url
        out = db.table_dictize(event, context)
        out.update({
            'status': status,
            'display_image_url': h.url_for_static(
                'uploads/pages/{}'.format(image_url),
                qualified=True
                ) if image_url and image_url[0:6] not in {'http:/', 'https:'}  else image_url,
            })
    else:
        raise tk.ObjectNotFound(_('Event item not found.')) 
    
    return out


@action
def events_delete(context, data_dict):
    tk.check_access("ckanext_event_delete", context)

    event = Event.get(data_dict.get('id'))
    if not event:
        raise tk.ObjectNotFound(_("Event not found"))
    event.delete()
    event.commit()
    return {"id": event.id, 'deleted': True}



@action
def news_delete(context, data_dict):
    tk.check_access("ckanext_news_delete", context, data_dict)
    news = News.get(data_dict.get('id'))

    if not news:
        raise tk.ObjectNotFound(_("News not found"))
    news.delete()
    news.commit()
    return {"success": True, 'id': news.id}


@action
def pages_delete(context, data_dict):
    tk.check_access("ckanext_pages_delete", context)
    id = data_dict.get('id')
    page = Page.get(id)
    if not page:
        raise tk.ObjectNotFound(_("Page not found"))
    page.delete()
    page.commit()
    return {"success": True, 'id': page.id}





def validate_main_page(section_id, data):
    # Get the schema for validation
    schema = main_page_schema()

    # Remove 'id' field if not required by schema
    data.pop('id', None)  # Prevent schema errors for 'id'

    # Validate the rest of the data
    errors = p.toolkit.navl_validate(data, schema)

    # Return validation result
    if errors:
        return False, errors
    return True, None



def get_main_page(section_id):
    return MainPage.get(id=section_id)


def update_main_page(section_id, data):
    section = MainPage.get(id=section_id)
    if section:
        section.main_title_1_ar = data.get('main_title_1_ar')
        section.main_title_1_en = data.get('main_title_1_en')
        section.main_title_2_ar = data.get('main_title_2_ar', '')
        section.main_title_2_en = data.get('main_title_2_en', '')
        section.main_brief_en = data.get('main_brief_en')
        section.main_brief_ar = data.get('main_brief_ar')
        model.Session.commit()
        return {"success": True}
    return {"success": False, "error": "Section not found"}


def main_page_edit(section_id):
    section_titles = {
        1: "Main Title & Brief",
        2: "Open Data Sector",
        3: "Indicators",
        4: "Open Data In Numbers",
        5: "Also Explore"
    }

    has_two_titles = True if int(section_id) == 1 else False

    section = MainPage.get(id=section_id)

    if not section:
        tk.h.flash_error('Section not found!')
        return tk.redirect_to('main_page')

    if tk.request.method == 'POST':
        action = tk.request.form.get('save') or tk.request.form.get('delete')

        if action == 'save':
            data = {
                "main_title_1_ar": tk.request.form['main_title_1_ar'],
                "main_title_1_en": tk.request.form['main_title_1_en'],
                "main_title_2_ar": tk.request.form.get('main_title_2_ar') if has_two_titles else None,
                "main_title_2_en": tk.request.form.get('main_title_2_en') if has_two_titles else None,
                "main_brief_en": tk.request.form['main_brief_en'],
                "main_brief_ar": tk.request.form['main_brief_ar'],
            }

            valid, errors = validate_main_page(section_id, data)
            if not valid:
                tk.h.flash_error(errors)
                return tk.redirect_to('pages.main_page_edit', section_id=section_id)

            update_main_page(section_id, data)
            tk.h.flash_success('Section updated successfully!')

        elif action == 'delete':
            tk.h.flash_error('Section deleted successfully!')
            return tk.redirect_to('main_page')

        return tk.redirect_to('main_page')

    return tk.render(
        'main_page/main_page_edit.html',
        section=section,
        has_two_titles=has_two_titles,
        section_title=section_titles.get(int(section_id), "Unknown Section")
    )


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

    return tk.render('main_page/main_page.html', sections=data)

def _main_page_show(context, data_dict):
    section_id = data_dict.get('section_id')

    out = db.MainPage.get(id=section_id)
    if out:
        out = db.table_dictize(out, context)
    return out or {}


@tk.side_effect_free
def main_page_show(context, data_dict):
    try:
        tk.check_access('is_content_editor', context)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _main_page_show(context, data_dict)


def events_edit(context, data_dict):
    event_id = data_dict.get('id')
    if event_id:
        # Fetch the event from the database
        event = model.Session.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise p.toolkit.ObjectNotFound(f"Event with ID {event_id} not found.")
    else:
        # Creating a new event
        event = Event()

    # Update the fields
    event.title_en = data_dict.get('title_en', event.title_en)
    event.title_ar = data_dict.get('title_ar', event.title_ar)
    event.start_date = data_dict.get('start_date', event.start_date)
    event.end_date = data_dict.get('end_date', event.end_date)
    event.brief_en = data_dict.get('brief_en', event.brief_en)
    event.brief_ar = data_dict.get('brief_ar', event.brief_ar)
    event.content_en = data_dict.get('content_en', event.content_en)
    event.content_ar = data_dict.get('content_ar', event.content_ar)
    event.image_url = data_dict.get('image_url', event.image_url)
    event.lang = data_dict.get('lang', event.lang)

    # Save the changes to the database
    model.Session.add(event)
    model.Session.commit()
    return event.as_dict()


def news_show(context, data_dict):
    tk.check_access('ckanext_news_show', context, data_dict)
    news_id = data_dict.get('id')
    if not news_id:
        raise tk.ValidationError({'id': ['Missing value']})

    news = News.get(news_id)

    if not news:
        raise tk.ObjectNotFound('News item not found')
    if news:
        image_url = news.image_url
        out = db.table_dictize(news, context)
        out.update({
            'display_image_url': h.url_for_static(
                'uploads/pages/{}'.format(image_url),
                qualified=True
                ) if image_url and image_url[0:6] not in {'http:/', 'https:'}  else image_url,
            })
    else:
        raise tk.ObjectNotFound(_('News item not found.')) 
    
    return out


# List Actions - Header Management
@tk.side_effect_free
def header_main_menu_list(context, data_dict):
    """List all main menu items."""
    tk.check_access('ckanext_header_management_access', context)

    menu_type = data_dict.get('menu_type')

    query = model.Session.query(
        HeaderMainMenu
    ).order_by(
        HeaderMainMenu.created.asc(),
        HeaderMainMenu.order
    )


    if menu_type:
        query = query.filter_by(menu_type=menu_type)

    return query.all()


def header_main_menu_parent_list(context, data_dict):
    """List all main menu parent items."""
    tk.check_access('ckanext_header_management_access', context)

    return model.Session.query(HeaderMainMenu).filter_by(parent_id=None, menu_type='menu').order_by(HeaderMainMenu.order).all()


def header_secondary_menu_parent_list(context, data_dict):
    """List all secondary menu parent items."""
    tk.check_access('ckanext_header_management_access', context)

    return model.Session.query(HeaderSecondaryMenu).filter_by(parent_id=None).order_by(HeaderSecondaryMenu.order).all()


@tk.side_effect_free
def header_secondary_menu_list(context, data_dict):
    """List all secondary menu items."""
    tk.check_access('ckanext_header_management_access', context)

    items = model.Session.query(HeaderSecondaryMenu).order_by(HeaderSecondaryMenu.order).all()

    return [item.as_dict() for item in items]


@tk.side_effect_free
def header_logo_get(context, data_dict):
    """Get header logo."""
    tk.check_access('ckanext_header_management_access', context)
    return model.Session.query(HeaderLogo).first()


# Update Actions - Header Management
def header_main_menu_toggle_visibility(context, data_dict):
    """Toggle visibility of a main menu item."""
    tk.check_access('ckanext_header_management_access', context)
    
    menu_item = model.Session.query(HeaderMainMenu).get(data_dict['id'])

    if not menu_item:
        raise tk.ObjectNotFound('Menu item not found')

    menu_item.is_visible = not menu_item.is_visible
    model.Session.commit()

    return menu_item.as_dict()


def header_main_menu_delete(context, data_dict):
    """Delete a main menu item."""
    tk.check_access('ckanext_header_management_access', context)
    
    menu_item = model.Session.query(HeaderMainMenu).get(data_dict['id'])

    if not menu_item:
        raise tk.ObjectNotFound('Menu item not found')

    # Check for children
    children = model.Session.query(HeaderMainMenu).filter_by(parent_id=menu_item.id).count()
    if children > 0:
        raise tk.ValidationError(
            {'id': 'Cannot delete menu item with child items'}
        )

    menu_item.delete()
    model.Session.commit()

    return {'message': 'Menu item deleted'}


def header_logo_update(context, data_dict):
    """Update a header logo."""
    tk.check_access('ckanext_header_management_access', context)

    model = context['model']
    logo = model.Session.query(HeaderLogo).get(data_dict['id'])

    if not logo:
        raise tk.ObjectNotFound('Header logo not found')

    if data_dict.get('logo_ar_upload'):
        upload_ar = uploader.get_uploader('header_logos')

        upload_ar.update_data_dict(
            data_dict,
            'logo_ar_url',
            'logo_ar_upload',
            'clear_logo_ar'
        )
        upload_ar.upload(uploader.get_max_image_size())

        logo_ar_url = data_dict.get('logo_ar_url')
        if logo_ar_url and logo_ar_url[0:6] not in {'http:/', 'https:'}:
            logo_ar_url = 'uploads/header_logos/{}'.format(logo_ar_url)
            logo.logo_ar = logo_ar_url

    if data_dict.get('logo_en_upload'):
        upload_en = uploader.get_uploader('header_logos')

        upload_en.update_data_dict(
            data_dict,
            'logo_en_url',
            'logo_en_upload',
            'clear_logo_en'
        )

        upload_en.upload(uploader.get_max_image_size())

        logo_en_url = data_dict.get('logo_en_url')
        if logo_en_url and logo_en_url[0:6] not in {'http:/', 'https:'}:
            logo_en_url = 'uploads/header_logos/{}'.format(logo_en_url)
            logo.logo_en = logo_en_url

    logo.modified = datetime.datetime.utcnow()
    model.Session.commit()

    return logo.as_dict()

def header_logo_delete(context, data_dict):
    """Delete a header logo."""
    tk.check_access('ckanext_header_management_access', context)
    
    logo = model.Session.query(HeaderLogo).get(data_dict['id'])

    if not logo:
        raise tk.ObjectNotFound('Logo not found')

    logo.delete()
    model.Session.commit()

    return {'message': 'Logo deleted'}


def header_logo_toggle_visibility(context, data_dict):
    """Toggle visibility of a header logo."""
    tk.check_access('ckanext_header_management_access', context)

    logo = model.Session.query(HeaderLogo).get(data_dict['id'])

    if not logo:
        raise tk.ObjectNotFound('Logo not found')

    logo.is_visible = not logo.is_visible
    model.Session.commit()

    return logo.as_dict()


def header_secondary_menu_delete(context, data_dict):
    """Delete a secondary menu item."""
    tk.check_access('ckanext_header_management_access', context)

    menu_item = model.Session.query(HeaderSecondaryMenu).get(data_dict['id'])

    if not menu_item:
        raise tk.ObjectNotFound('Menu item not found')

    menu_item.delete()
    model.Session.commit()

    return {'message': 'Menu item deleted'}


def header_secondary_menu_toggle_visibility(context, data_dict):
    """Toggle visibility of a secondary menu item."""
    tk.check_access('ckanext_header_management_access', context)

    menu_item = model.Session.query(HeaderSecondaryMenu).get(data_dict['id'])

    if not menu_item:
        raise tk.ObjectNotFound('Menu item not found')

    menu_item.is_visible = not menu_item.is_visible
    model.Session.commit()

    return menu_item.as_dict()


def header_logo_upload(context, data_dict):
    """Upload header logos."""
    tk.check_access('ckanext_header_management_access', context)

    # Validate the data
    data, errors = tk.navl_validate(
        data_dict,
        header_logo_upload_schema(),
        context
    )

    if errors:
        raise tk.ValidationError(errors)

    # Handle file uploads
    def handle_logo_upload(field_name):
        upload = tk.uploader.get_uploader('header_logos')

        # Check if file is an image
        if field_name in data_dict:
            upload_field = data_dict[field_name]
            if hasattr(upload_field, 'filename'):
                if not upload_field.filename.lower().endswith(
                        ('.png', '.jpg', '.jpeg', '.gif')
                ):
                    raise tk.ValidationError({
                        field_name: 'File must be an image (PNG, JPG, or GIF)'
                    })

        upload.update_data_dict(
            data_dict,
            field_name,
            f'{field_name}_url',
            'clear_upload'
        )

        try:
            upload.upload(max_size=2)  # 2MB max size
            return upload.filename
        except Exception as e:
            raise tk.ValidationError({field_name: str(e)})

    logo_en_filename = handle_logo_upload('logo_en_upload')
    logo_ar_filename = handle_logo_upload('logo_ar_upload')

    # Update or create logo record
    
    logo = model.HeaderLogo.get() or model.HeaderLogo()

    if logo_en_filename:
        logo.logo_en = logo_en_filename
    if logo_ar_filename:
        logo.logo_ar = logo_ar_filename

    logo.save()
    return logo.as_dict()


def header_main_menu_create(context, data_dict):
    """Create a new main menu item with validation."""
    tk.check_access('ckanext_header_management_access', context)

    # Validate the data
    data, errors = tk.navl_validate(
        data_dict,
        header_menu_schema(),
        context
    )

    if errors:
        raise tk.ValidationError(errors)

    if parent_id := data.get('parent_id'):
        parent = model.Session.query(HeaderMainMenu).get(parent_id)
        errors = []

        if not parent:
            errors.append('Parent menu item not found')

        if parent.menu_type != 'menu':
            errors.append('Parent must be a menu type item')
        if parent.parent_id:
            errors.append('Maximum nesting level exceeded')

        if errors:
            raise tk.ValidationError({'parent_id': errors})

    if (order := data.get('order')) and (menu_type := data.get('menu_type')):
        if menu_type == 'menu':
            if model.Session.query(HeaderMainMenu).filter_by(order=order, parent_id=parent_id).first():
                raise tk.ValidationError({'order': ['Order already taken']})
        elif menu_type == 'link':
            if model.Session.query(HeaderMainMenu).filter_by(order=order).first():
                raise tk.ValidationError({'order': ['Order already taken']})

    menu_item = HeaderMainMenu(
        title_en=data['title_en'],
        title_ar=data['title_ar'],
        link_en=data['link_en'],
        link_ar=data['link_ar'],
        menu_type=data['menu_type'],
        parent_id=parent_id or None,
        order=data.get('order', 0),
        is_visible=data.get('is_visible', True)
    )

    menu_item.save()
    return menu_item.as_dict()

def header_main_menu_show(context, data_dict):
    """Show a main menu item."""
    tk.check_access('ckanext_header_management_access', context)

    menu_item = model.Session.query(HeaderMainMenu).get(data_dict['id'])

    if not menu_item:
        raise tk.ObjectNotFound('Menu item not found')

    menu_item_dict = menu_item.as_dict()
    menu_item_dict['parent'] = menu_item.parent.as_dict() if menu_item.parent else None
    return menu_item_dict

def header_main_menu_edit(context, data_dict):
    """Edit a main menu item."""
    tk.check_access('ckanext_header_management_access', context)

    menu_item = model.Session.query(HeaderMainMenu).get(data_dict['id'])

    if not menu_item:
        raise tk.ObjectNotFound('Menu item not found')

    data, errors = tk.navl_validate(
        data_dict,
        header_menu_schema(),
        context
    )

    if errors:
        raise tk.ValidationError(errors)

    if parent_id := data.get('parent_id'):
        parent = model.Session.query(HeaderMainMenu).get(parent_id)
        errors = []

        if not parent:
            errors.append('Parent menu item not found')
        if parent_id == menu_item.id:
            errors.append('Cannot set parent to self')
        if parent.menu_type != 'menu':
            errors.append('Parent must be a menu type item')
        if parent.parent_id:
            errors.append('Maximum nesting level exceeded')

        if errors:
            raise tk.ValidationError({'parent_id': errors})

        menu_item.parent_id = parent_id

    if (order := data.get('order')) and (order != menu_item.order):
        if parent_id:
            if model.Session.query(HeaderMainMenu).filter_by(order=order, parent_id=parent_id).first():
                raise tk.ValidationError({'order': ['Order already taken']})
        elif model.Session.query(HeaderMainMenu).filter_by(order=order).first():
                raise tk.ValidationError({'order': ['Order already taken']})


    menu_item.title_en = data['title_en']
    menu_item.title_ar = data['title_ar']
    menu_item.link_en = data['link_en']
    menu_item.link_ar = data['link_ar']
    menu_item.menu_type = data['menu_type']
    menu_item.order = data.get('order', 0)
    menu_item.is_visible = data.get('is_visible', True)

    model.Session.commit()
    return menu_item.as_dict()

def header_secondary_menu_edit(context, data_dict):
    """Edit a secondary menu item."""
    tk.check_access('ckanext_header_management_access', context)

    menu_item = model.Session.query(HeaderSecondaryMenu).get(data_dict['id'])

    if not menu_item:
        raise tk.ObjectNotFound('Menu item not found')

    data, errors = tk.navl_validate(
        data_dict,
        header_menu_schema(),
        context
    )

    if errors:
        raise tk.ValidationError(errors)

    if parent_id := data.get('parent_id'):
        parent = model.Session.query(HeaderSecondaryMenu).get(parent_id)
        errors = []

        if not parent:
            errors.append('Parent menu item not found')
        if parent_id == menu_item.id:
            errors.append('Cannot set parent to self')
        if parent.menu_type != 'menu':
            errors.append('Parent must be a menu type item')
        if parent.parent_id:
            errors.append('Maximum nesting level exceeded')

        if errors:
            raise tk.ValidationError({'parent_id': errors})

        menu_item.parent_id = parent_id

    if (order := data.get('order')) and (order != menu_item.order):
        if parent_id:
            if model.Session.query(HeaderSecondaryMenu).filter_by(order=order, parent_id=parent_id).first():
                raise tk.ValidationError({'order': ['Order already taken']})
        elif model.Session.query(HeaderSecondaryMenu).filter_by(order=order).first():
                raise tk.ValidationError({'order': ['Order already taken']})


    menu_item.title_en = data['title_en']
    menu_item.title_ar = data['title_ar']
    menu_item.link_en = data['link_en']
    menu_item.link_ar = data['link_ar']
    menu_item.menu_type = data['menu_type']
    menu_item.order = data.get('order', 0)
    menu_item.is_visible = data.get('is_visible', True)

    model.Session.commit()
    return menu_item.as_dict()

def header_secondary_menu_show(context, data_dict):
    """Show a secondary menu item."""
    tk.check_access('ckanext_header_management_access', context)

    menu_item = model.Session.query(HeaderSecondaryMenu).get(data_dict['id'])

    if not menu_item:
        raise tk.ObjectNotFound('Menu item not found')

    return menu_item.as_dict()

def header_secondary_menu_create(context, data_dict):
    """Create a new secondary menu item with validation."""
    tk.check_access('ckanext_header_management_access', context)

    data, errors = tk.navl_validate(
        data_dict,
        header_menu_schema(),
        context
    )

    if errors:
        raise tk.ValidationError(errors)

    menu_item = HeaderSecondaryMenu(
        title_en=data['title_en'],
        title_ar=data['title_ar'],
        link_en=data['link_en'],
        link_ar=data['link_ar'],
        menu_type=data['menu_type'],
        parent_id=data.get('parent_id') or None,
        order=data.get('order', 0),
        is_visible=data.get('is_visible', True)
    )

    if parent_id := data.get('parent_id'):
        parent = model.Session.query(HeaderSecondaryMenu).get(parent_id)
        errors = []

        if not parent:
            errors.append('Parent menu item not found')
        if parent_id == menu_item.id:
            errors.append('Cannot set parent to self')
        if parent.menu_type != 'menu':
            errors.append('Parent must be a menu type item')
        if parent.parent_id:
            errors.append('Maximum nesting level exceeded')

        if errors:
            raise tk.ValidationError({'parent_id': errors})

        menu_item.parent_id = parent_id

    if order := data.get('order'):
        if parent_id:
            if model.Session.query(HeaderSecondaryMenu).filter_by(order=order, parent_id=parent_id).first():
                raise tk.ValidationError({'order': ['Order already taken']})
        elif model.Session.query(HeaderSecondaryMenu).filter_by(order=order).first():
            raise tk.ValidationError({'order': ['Order already taken']})

    menu_item.save()
    return menu_item.as_dict()


def single_image_upload(context, data_dict):
    tk.check_access('is_content_editor', context)

    old_filename = data_dict.get('old_filename', None)
    old_filename = old_filename if old_filename and old_filename[0:6] not in {'http:/', 'https:'} else None
    upload = uploader.get_uploader('pages', old_filename)

    data_dict.update(data_dict.get('__extras', {}))
    upload.update_data_dict(data_dict, 'image_url', 'image_upload', 'clear_upload')
    upload.upload(uploader.get_max_image_size())


    return data_dict