from ckan.plugins import toolkit as tk
from ckanext.pages.db import Event, News, Page
from ckanext.pages.footer.model.footer import FooterBanner, FooterColumnLinks, FooterSocialMedia
Invalid = tk.Invalid
_ = tk._

import glob
import os

UPLOADS_DIR = '/var/lib/ckan/default/storage/uploads'


def is_file_uploaded(file_storage):
    """Check if a *new* file is uploaded."""
    return (
        file_storage is not None
        and hasattr(file_storage, 'filename')
        and file_storage.filename.strip() != ''
    )


def is_already_uploaded(filename):
    pattern = os.path.join(UPLOADS_DIR, '**', filename)
    return any(glob.iglob(pattern, recursive=True))


def is_url(value):
    """Check if the value is a valid URL (not a data URI or base64)."""
    if isinstance(value, str):
        return value.startswith('http://') or value.startswith('https://')
    return False


def image_upload_or_valid_url(key, data, errors, context):
    upload_field = context.get('upload_field', 'image_upload')
    value = data.get(key)
    extras = data.get(('__extras',), {})
    file_storage = extras.get(upload_field)


    # Case 1: new file uploaded
    if is_file_uploaded(file_storage):
        return

    # Case 2: already uploaded file submitted again
    if is_already_uploaded(value):
        return
    
    # Case 3: no file uploaded but value is a valid URL
    if is_url(value):
        return

    errors[key].append(_('Invalid image url %s ...' %value[:30]))



def image_upload_or_valid_url_logo_en(key, data, errors, context):
    context['upload_field'] = 'logo_en_upload'
    image_upload_or_valid_url(key, data, errors, context)


def image_upload_or_valid_url_logo_ar(key, data, errors, context):
    context['upload_field'] = 'logo_ar_upload'
    image_upload_or_valid_url(key, data, errors, context)



def column_number_validator(value):
    if value in [2,3]:
        return value
    raise Invalid(_('Invalid Column Number.'))


def column_link_id_validator(value):
    record = FooterColumnLinks.get(id=value)
    if record:  return value
    raise Invalid(_('Invalid Id. Record not found.'))


def column_order_validator(key, data, errors, context):
    id = data.get(('id',), None)
    column_number = data.get(('column_number',))
    order = data.get(key)

    try:
        order = int(order)
        if order > 10:
            errors[key].append(_('Invalid order. Order should be at max 10.'))
        if order == 0:
            errors[key].append(_('Invalid order. The order should be greater than zero'))

    except (ValueError, TypeError):
        return  # Let natural_number_validator handle this

    if column_number is None:
        return
    
    query = FooterColumnLinks.filter(column_number=column_number, order=order)

    if id:
        query = query.filter(FooterColumnLinks.id != id)

    if query.first():
        errors[key].append(_('Invalid order. Order already taken.'))


def social_media_id_validator(value):
    record = FooterSocialMedia.get(id=value)
    if record:  return value
    raise Invalid(_('Invalid Id. Record not found.'))


def social_media_order_validator(key, data, errors, context):
    id = data.get(('id',), None)
    value = data.get(key)

    try:
        value = int(value)
        if value > 10:
            errors[key].append(_('Invalid order. Order should be at max 10.'))
        if value == 0:
            errors[key].append(_('Invalid order. The order should be greater than zero'))

    except (ValueError, TypeError):
        return

    query = FooterSocialMedia.filter(order = value)
    if id:
        query = query.filter(FooterSocialMedia.id != id)

    if query.first():
        errors[key].append(_('Invalid order. Order already taken.'))


def banner_id_validator(value):
    record = FooterBanner.get(id=value)
    if record:  return value
    raise Invalid(_('Invalid Id. Record not found.'))


def banner_order_validator(key, data, errors, context):
    id = data.get(('id',), None)
    value = data.get(key)

    # Ensure value is an integer before querying
    try:
        value = int(value)
        if value > 10:
            errors[key].append(_('Invalid order. Order should be at max 10.'))
        if value == 0:
            errors[key].append(_('Invalid order. The order should be greater than zero'))
    except (ValueError, TypeError):
        return  # Let the natural_number_validator handle invalid input

    query = FooterBanner.filter(order = value)
    if id:
        query = query.filter(FooterBanner.id != id)

    if query.first():
        errors[key].append(_('Invalid order. Order already taken.'))


def link_target_validator(value):
    if value in ['_self', '_blank']:
        return value
    raise Invalid(_('Invalid Target Selected.'))



def pages_name_validator(key, data, errors, context):
    _class_name_validator(key, data, errors, context, Page)


def event_name_validator(key, data, errors, context):
    _class_name_validator(key, data, errors, context, Event)


def news_name_validator(key, data, errors, context):
    _class_name_validator(key, data, errors, context, News)



def _class_name_validator(key, data, errors, context, cls):
    id = data.get(('id',), None)
    name = data.get(key)

    instance = cls.get(id)
    if id and instance and instance.name == name:    return
    if bool(cls.get(name)):
        errors.get(key, []).append(_('Invalid name. Name already exists'))


