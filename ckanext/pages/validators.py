import ckan.plugins as p
import ckan.lib.navl.dictization_functions as df
from ckanext.pages import db
tk = p.toolkit
_ = tk._

def page_name_validator(key, data, errors, context):
    session = context['session']
    page = context.get('page')
    group_id = context.get('group_id')
    if page and page == data[key]:
        return

    query = session.query(db.Page.name).filter_by(name=data[key], group_id=group_id)
    result = query.first()
    if result:
        errors[key].append(
            p.toolkit._('Page name already exists in database'))


def not_empty_if_blog(key, data, errors, context):
    value = data.get(key)
    if data.get(('page_type',), '') == 'blog':
        if value is df.missing or not value:
            errors[key].append('Publish Date Must be supplied')


def validate_image_upload(key, data, errors, context, file_size=2):
    """Validator for logo uploads."""
    value = data.get(key)
    if not value:
        return

    # Check file type
    if value.type not in ['image/jpeg', 'image/png', 'image/gif']:
        errors[key].append(
            'File must be a valid image file (JPEG, PNG, or GIF)'
        )
        return

    # Check file size (2MB max)
    if value.content_length > file_size * 1024 * 1024:
        errors[key].append(
            'File size must be less than 2MB'
        )
        return


from ckanext.pages.db import HeaderMainMenu

def header_parent_id_validator(key, data, errors, context):
    value = data.get(key)
    id = data.get(('id',), None)

    if not value:
        data[key] = None
        return
    
    parent = HeaderMainMenu.get(id=value)


    if parent is None:
        errors[key].append(_('Parent menu item not found'))
        return
    
    if parent.menu_type != 'menu':
        errors[key].append('Parent must be a menu type item')
        return
    
    if id and parent.id == id:
        errors[key].append('Cannot set parent to self')
        return
    

def header_menu_id_validator(cls):
    def func(key, data, errors, context):
        value = data.get(key)
        menu_item = cls.get(id=value)

        if not menu_item:
            errors[key].append(_('Menu item not found'))
            return
    return func


def header_order_validator(header_class):
    def header_class_order_validator(key, data, errors, context):
        id = data.get(('id',), None)
        parent_id = data.get(('parent_id',), None) or None
        order = data.get(key)


        query = header_class.filter(order=order, parent_id= parent_id)

        if id:
            query = query.filter(header_class.id != id)


        if query.first():
            errors[key].append(_('Invalid order. Order already taken.'))

    
    return header_class_order_validator


def max_length_validator(length):
    def func(key, data, errors, context):
        value = data.get(key)
        if value and len(value) > length:
            errors[key].append(
                _('Value must be at most %s characters long. Current length is %s.') % (length, len(value))
            )
    return func

def min_length_validator(length):
    def func(key, data, errors, context):
        value = data.get(key)
        if value and len(value) < length:
            errors[key].append(
                _('Value must be at least %s characters long. Current length is %s.') % (length, len(value))
            )
    return func