import ckanext.pages.utils as utils
from ckan import model
from ckanext.pages.db import MainPage
from ckanext.pages.db import Page
from flask import Blueprint, render_template, request, redirect, url_for
from flask import g
from flask import jsonify
from ckan.plugins import toolkit as tk
import ckan.lib.helpers as h
from ckan.types import Context
from ckan.common import current_user, _
from typing import Any, Optional, Union, cast

pages = Blueprint('pages', __name__, url_prefix="/cms")


@pages.before_request
def set_current_section():
    if request.endpoint == 'pages.pages_index' or request.endpoint == 'pages.new' or request.endpoint == 'pages.edit':
        g.current_section = 'pages'
    elif request.endpoint == 'pages.news_index' or request.endpoint == 'pages.news_new':
        g.current_section = 'news'
    elif request.endpoint == 'pages.events' or request.endpoint == 'pages.events_new':
        g.current_section = 'events'
    elif request.endpoint == 'pages.main_page' or request.endpoint == 'pages.main_page_edit':
        g.current_section = 'main_page'


def _get_context():
    context = cast(Context, {
        u'model': model,
        u'session': model.Session,
        u'user': current_user.name,
        u'auth_user_obj': current_user,
    })
    return context



def upload():
    return utils.pages_upload()


def main_page():
    return utils.main_page()


def main_page_edit(section_id, data=None, errors=None, error_summary=None):
    return utils.main_page_edit(section_id, data, errors, error_summary)


def get_main_page(section_id):
    return MainPage.get(id=section_id)



_ = tk._
config = tk.config

def internal_urls():
    current_lang = h.lang()
    data = [{
            'title': _('Datasets'),
            'link_en': config.get('ckan.site_url') + '/en' +  h.url_for('dataset.search').replace('/' + current_lang + '/', '/'),
            'link_ar': config.get('ckan.site_url') + '/ar' +  h.url_for('dataset.search').replace('/' + current_lang + '/', '/'),
        },
        {
            'title': _('Government Entities'),
            'link_en': config.get('ckan.site_url') + '/en' +  h.url_for('organization.index').replace('/' + current_lang + '/', '/'),
            'link_ar': config.get('ckan.site_url') + '/ar' +  h.url_for('organization.index').replace('/' + current_lang + '/', '/'),
        },
        {
            'title': _('Sectors'),
            'link_en': config.get('ckan.site_url') + '/en' +  h.url_for('group.index').replace('/' + current_lang + '/', '/'),
            'link_ar': config.get('ckan.site_url') + '/ar' +  h.url_for('group.index').replace('/' + current_lang + '/', '/'),
        },
        {
            'title': _('Dashboard'),
            'link_en': config.get('ckan.site_url') + '/en' +  h.url_for('ogddashboard.router').replace('/' + current_lang + '/', '/'),
            'link_ar': config.get('ckan.site_url') + '/ar' +  h.url_for('ogddashboard.router').replace('/' + current_lang + '/', '/'),
        },
        {
            'title': _('Reuses'),
            'link_en': config.get('ckan.site_url') + '/en' +  h.url_for('showcase_blueprint.index').replace('/' + current_lang + '/', '/'),
            'link_ar': config.get('ckan.site_url') + '/ar' +  h.url_for('showcase_blueprint.index').replace('/' + current_lang + '/', '/'),
        },
        {
            'title': _('Request New Dataset'),
            'link_en': config.get('ckan.site_url') + '/en' +  h.url_for('requests.new').replace('/' + current_lang + '/', '/'),
            'link_ar': config.get('ckan.site_url') + '/ar' +  h.url_for('requests.new').replace('/' + current_lang + '/', '/'),
        },
        {
            'title': _('Report an Error'),
            'link_en': config.get('ckan.site_url') + '/en' +  h.url_for('issues.new').replace('/' + current_lang + '/', '/'),
            'link_ar': config.get('ckan.site_url') + '/ar' +  h.url_for('issues.new').replace('/' + current_lang + '/', '/'),
        },
        {
            'title': _('API Guide'),
            'link_en': config.get('ckan.site_url') + '/en' +  h.url_for('home_page.api_guide').replace('/' + current_lang + '/', '/'),
            'link_ar': config.get('ckan.site_url') + '/ar' +  h.url_for('home_page.api_guide').replace('/' + current_lang + '/', '/'),
        },
        {
            'title': _('Submit new Reuse'),
            'link_en': config.get('ckan.site_url') + '/en' +  h.url_for('showcase_blueprint.new').replace('/' + current_lang + '/', '/'),
            'link_ar': config.get('ckan.site_url') + '/ar' +  h.url_for('showcase_blueprint.new').replace('/' + current_lang + '/', '/'),
        },
        {
            'title': _('News List'),
            'link_en': config.get('ckan.site_url') + '/en' +  h.url_for('home_page.news').replace('/' + current_lang + '/', '/'),
            'link_ar': config.get('ckan.site_url') + '/ar' +  h.url_for('home_page.news').replace('/' + current_lang + '/', '/'),
        },
        {
            'title': _('Events List'),
            'link_en': config.get('ckan.site_url') + '/en' +  h.url_for('home_page.events').replace('/' + current_lang + '/', '/'),
            'link_ar': config.get('ckan.site_url') + '/ar' +  h.url_for('home_page.events').replace('/' + current_lang + '/', '/'),
        },
    ]
    return tk.render('ckanext_pages/internal_urls.html', {'data': data})
    

# blueprints
from ckanext.pages import blueprint_pages
from ckanext.pages import blueprint_events
from ckanext.pages import blueprint_news

blueprint_news.register_news(pages)
blueprint_pages.register_pages(pages)
blueprint_events.register_events(pages)



pages.add_url_rule("/main_page/edit/<section_id>", view_func=main_page_edit, endpoint="main_page_edit",
                   methods=['GET', 'POST'])

pages.add_url_rule("/main_page", view_func=main_page, endpoint="main_page")


# File Uploads
pages.add_url_rule("/pages_upload", view_func=upload, methods=['POST'])


pages.add_url_rule("/internal-urls", view_func=internal_urls, endpoint='internal_urls',
                   methods=['GET'])



def get_blueprints():
    return [pages]
