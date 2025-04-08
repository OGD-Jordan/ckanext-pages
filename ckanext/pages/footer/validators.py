from ckan.plugins import toolkit as tk
from ckanext.pages.db import Event, News, Page
from ckanext.pages.footer.model.footer import FooterBanner, FooterColumnLinks, FooterSocialMedia
Invalid = tk.Invalid
_ = tk._




def column_number_validator(value):
    if value in [2,3]:
        return value
    raise Invalid(_('Invalid Column Number.'))


def column_link_id_validator(value):
    record = FooterColumnLinks.get(id=value)
    if record:  return value
    raise Invalid(_('Invalid Id. Record not found.'))


def column_order_validator(key, data, errors, context):
    id = data.get(('id',),None)
    column_number_key = ('column_number',)
    column_number = data.get(column_number_key)

    record = FooterColumnLinks.get(column_number=column_number, order = data[key]) and not FooterColumnLinks.get(column_number=column_number, order = data[key], id=id)
    if record:
        raise Invalid(_('Invalid order. Order already taken.'))


def social_media_id_validator(value):
    record = FooterSocialMedia.get(id=value)
    if record:  return value
    raise Invalid(_('Invalid Id. Record not found.'))


def social_media_order_validator(key, data, errors, context):
    id = data.get(('id',),None)
    value = data[key]
    record = FooterSocialMedia.get(order=value) and not FooterSocialMedia.get(order=value, id=id)
    if record:  
        raise Invalid(_('Invalid order. Order already taken.'))
    return value



def banner_id_validator(value):
    record = FooterBanner.get(id=value)
    if record:  return value
    raise Invalid(_('Invalid Id. Record not found.'))


def banner_order_validator(key, data, errors, context):
    id = data.get(('id',),None)
    value = data[key]
    record = FooterBanner.get(order=value) and not FooterBanner.get(order=value, id=id)
    if record:  
        raise Invalid(_('Invalid order. Order already taken.'))
    return value


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


