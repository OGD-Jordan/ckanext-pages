import ckan.plugins as p

import ckan.authz as authz

from ckanext.pages import db, utils
from ckan.plugins import toolkit as tk

_ = tk._
def sysadmin(context, data_dict):
    return {'success':  False}

def is_content_editor(context, data_dict):
    return authz.is_authorized('is_content_editor', context)

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
@p.toolkit.auth_allow_anonymous_access
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


