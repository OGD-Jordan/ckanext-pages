import ckan.plugins as p
from ckanext.pages.footer.validators import event_name_validator, news_name_validator, pages_name_validator
from ckanext.pages.validators import page_name_validator, not_empty_if_blog, validate_image_upload
from ckanext.pages.interfaces import IPagesSchema
from ckan.plugins.toolkit import get_validator
from datetime import datetime
from ckan.common import _

tk = p.toolkit

ignore_empty = p.toolkit.get_validator('ignore_empty')
ignore_missing = p.toolkit.get_validator('ignore_missing')
not_empty = p.toolkit.get_validator('not_empty')
isodate = p.toolkit.get_validator('isodate')
name_validator = p.toolkit.get_validator('name_validator')
unicode_safe = p.toolkit.get_validator('unicode_safe')
convert_to_extras = p.toolkit.get_converter('convert_to_extras')

def publish_date_in_future(key, data, errors, context):
    publish_date = data.get(key)

    if not publish_date:
        return

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    if publish_date < today:
        errors[key].append(_("Publish date must be today or in the future"))

def default_pages_schema():

    return {
        'id': [ignore_empty, unicode_safe],
        'title_en': [not_empty, unicode_safe, get_validator('validate_english_text')],
        'title_ar': [not_empty, unicode_safe, get_validator('validate_arabic_text')],
        'name': [not_empty, name_validator, pages_name_validator],
        'content_en': [not_empty, unicode_safe],
        'content_ar': [not_empty, unicode_safe],
        'image_url': [ignore_missing, unicode_safe],
        'order': [ignore_missing, unicode_safe],
        'private': [ignore_missing, p.toolkit.get_validator('boolean_validator')],
        'user_id': [ignore_missing, unicode_safe],
        'publish_date': [ignore_missing, isodate, publish_date_in_future],
        'page_type': [ignore_missing, unicode_safe],
        'created': [ignore_missing, isodate],
        'modified': [ignore_missing, isodate],
        'extras': [ignore_missing, unicode_safe],
        'hidden':[ignore_missing, p.toolkit.get_validator('boolean_validator')],  
    }

def start_date_less_than_end_date(key, data, errors, context):
    start = data.get(('start_date',))
    end = data.get(('end_date',))

    if start and end:
        try:
            start_dt = datetime.fromisoformat(start) if isinstance(start, str) else start
            end_dt = datetime.fromisoformat(end) if isinstance(end, str) else end

            if start_dt > end_dt:
                errors[key].append(tk._("Start date must be less than end date."))
        except ValueError:
            pass


def default_events_schema():
    return {
        'id': [ignore_empty, unicode_safe],
        'title_en': [not_empty, unicode_safe, get_validator('validate_english_text')],
        'title_ar': [not_empty, unicode_safe, get_validator('validate_arabic_text')],
        'name': [not_empty, name_validator, event_name_validator],
        'start_date': [not_empty, isodate, start_date_less_than_end_date],
        'end_date': [not_empty, isodate],
        'brief_ar': [ignore_missing, unicode_safe, get_validator('validate_arabic_text')],
        'brief_en': [ignore_missing, unicode_safe, get_validator('validate_english_text')],
        'content_en': [ignore_missing, unicode_safe],
        'content_ar': [ignore_missing, unicode_safe],
        'image_url': [ignore_missing, unicode_safe],
        'lang': [ignore_missing, unicode_safe],
    }

def default_news_schema():
    return {
        'id': [ignore_empty, unicode_safe],
        'title_en': [not_empty, unicode_safe, get_validator('validate_english_text')],
        'title_ar': [not_empty, unicode_safe, get_validator('validate_arabic_text')],
        'name': [not_empty, name_validator, news_name_validator],
        'news_date': [not_empty, isodate],
        'brief_ar': [not_empty, unicode_safe, get_validator('validate_arabic_text')],
        'brief_en': [not_empty, unicode_safe, get_validator('validate_english_text')],
        'content_en': [not_empty, unicode_safe],
        'content_ar': [not_empty, unicode_safe],
        'image_url': [not_empty, unicode_safe],
    }


def main_page_schema(id=None):
    schema = {
        'id': [not_empty],  # Mandatory ID
        'main_title_1_ar': [not_empty, unicode_safe, get_validator('validate_arabic_text')],
        'main_title_1_en': [not_empty, unicode_safe, get_validator('validate_english_text')],
        'main_brief_en': [unicode_safe, get_validator('validate_english_text')],
        'main_brief_ar': [unicode_safe, get_validator('validate_arabic_text')],
    }
    if id == 1:  # Conditional for section 1
        schema['main_title_2_ar'] = [ignore_missing, unicode_safe]
        schema['main_title_2_en'] = [ignore_missing, unicode_safe]
    else:
        schema['main_title_2_ar'] = [ignore_missing]
        schema['main_title_2_en'] = [ignore_missing]
    return schema


def update_pages_schema(schema = default_pages_schema, **kwargs):
    if kwargs:
        schema = schema(**kwargs)
    else:
        schema = schema()
    for plugin in p.PluginImplementations(IPagesSchema):
        if hasattr(plugin, 'update_pages_schema'):
            schema = plugin.update_pages_schema(schema)
            print("Schema Used for Validation:", schema)
    return schema

def update_news_schema(schema = default_news_schema, **kwargs):
    if kwargs:
        schema = schema(**kwargs)
    else:
        schema = schema()
    for plugin in p.PluginImplementations(IPagesSchema):
        if hasattr(plugin, 'update_news_schema'):
            schema = plugin.update_news_schema(schema)
            print("Schema Used for Validation:", schema)
    return schema

def update_events_schema(schema = default_events_schema, **kwargs):
    if kwargs:
        schema = schema(**kwargs)
    else:
        schema = schema()
    for plugin in p.PluginImplementations(IPagesSchema):
        if hasattr(plugin, 'update_events_schema'):
            schema = plugin.update_events_schema(schema)
            print("Schema Used for Validation:", schema)
    return schema


def header_logo_schema():
    return {
        'id': [ignore_missing, unicode_safe],
        'logo_en': [ignore_missing, unicode_safe],
        'logo_ar': [ignore_missing, unicode_safe]
    }


def link_required_if_link_type_or_menu_child(key, data, errors, context):
    menu_type = data.get(('menu_type',))
    parent = data.get(('parent_id',))
    value = data.get(key)

    if (menu_type == 'link' or bool(parent)) and not value:
        errors[key].append(tk._('Missing value'))


def header_menu_schema():
    return {
        'id': [ignore_missing, unicode_safe],
        'title_en': [not_empty, unicode_safe, get_validator('validate_english_text')],
        'title_ar': [not_empty, unicode_safe, get_validator('validate_arabic_text')],
        'link_en': [ignore_missing, unicode_safe, link_required_if_link_type_or_menu_child],
        'link_ar': [ignore_missing, unicode_safe, link_required_if_link_type_or_menu_child],
        'menu_type': [not_empty, unicode_safe, p.toolkit.get_validator('one_of')(['link', 'menu'])],
        'parent_id': [ignore_missing, unicode_safe],
        'order': [ignore_missing, p.toolkit.get_validator('int_validator')],
        'is_visible': [ignore_missing, p.toolkit.get_validator('boolean_validator')]
    }


def header_logo_upload_schema():
    """Schema for logo upload validation."""
    return {
        'logo_en_upload': [ignore_missing, unicode_safe, validate_image_upload],
        'logo_ar_upload': [ignore_missing, unicode_safe, validate_image_upload],
        'clear_upload': [ignore_missing, p.toolkit.get_validator('boolean_validator')]
    }
