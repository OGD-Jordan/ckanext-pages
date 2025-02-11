import ckan.plugins as p

import ckan.authz as authz

from ckanext.pages import db, utils
from ckan.plugins import toolkit as tk

_ = tk._
def sysadmin(context, data_dict):
    return {'success':  False}

def is_content_editor(context, data_dict):
    return authz.is_authorized('is_content_editor')

@p.toolkit.auth_allow_anonymous_access
def anyone(context, data_dict):
    return {'success': True}


# @tk.auth_sysadmins_check
def page_data_coordinator(context, data_dict):
    if authz.auth_not_logged_in(context):
        return {'success': False, 'msg': _('User not found')}

    return {'success': utils.is_data_coordinator(context)}



@p.toolkit.auth_allow_anonymous_access
def page_privacy(context, data_dict):
    page = data_dict.get('id')
    out = db.Page.get(page)
    if (out and out.private is False) or authz.is_authorized_boolean('is_content_editor', context):
        return {'success':  True}

    return {'success': False}    

from datetime import datetime
def news_privacy(context, data_dict):
    if authz.is_authorized_boolean('is_content_editor', context):
        return {'success':  True}
    
    id = data_dict.get('id')
    news = db.News.get(id)

    if not news or news.hidden or news.news_date > datetime.now():
        return {'success': False}    
    
    return {'success':  True}



pages_update = is_content_editor
pages_delete = is_content_editor
pages_list = is_content_editor
pages_upload = is_content_editor
pages_show = page_privacy



def header_management_access(context, data_dict):
    """
    Only sysadmin and content writers can manage headers
    """
    # todo: remove this line
    # return {'success': True}
    user = context.get('auth_user_obj')
    if not user:
        return {'success': False}

    is_sysadmin = user.sysadmin
    is_content_writer = user.has_role('content_writer') if hasattr(user, 'has_role') else False

    return {'success': is_sysadmin or is_content_writer}