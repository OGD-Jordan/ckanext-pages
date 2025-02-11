# encoding: utf-8
from __future__ import annotations

from ckanext.pages import utils
from flask import Blueprint, request
from ckan.lib.helpers import helper_functions as h


import logging
import ckan.lib.base as base
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckan.model as model


from typing import Any, Optional, Union, cast
from flask import Blueprint
from flask.views import MethodView
from ckan.common import current_user, _, request

from ckan.views.home import CACHE_PARAMETERS
from ckan.types import Context, Response
from flask import request
from functools import partial
from ckan.lib.helpers import Page


_get_action = logic.get_action
_tuplize_dict = logic.tuplize_dict
_clean_dict = logic.clean_dict
_parse_params = logic.parse_params
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


log = logging.getLogger(__name__)


def index(page_type='page'):
    data_dict = {
        'page_type': page_type,
        'sort': request.args.get('sort', 'title_en asc')
    }

    tk.g.pages_dict = tk.get_action('ckanext_pages_list')(
        _get_context(), data_dict
    )

    tk.g.page = Page(
        collection=tk.g.pages_dict,
        page=tk.request.args.get('page', 1),
        url=h.pager_url,
        items_per_page=20
    )
    
    return tk.render('ckanext_pages/pages_list.html', extra_vars={"pages": tk.g.pages_dict})


def show(id, page_type='page'):
    tk.c.page_type = page_type

    if not id:
        h.flash_error(_('Page id not specified.'))
        return h.redirect_to('pages.pages_index')
    _page = tk.get_action('ckanext_pages_show')(
        context=_get_context(),
        data_dict={'id': id}
    )
    if _page is None:
        h.flash_error(_('Page not found.'))
        return h.redirect_to('pages.pages_index')

    tk.c.page = _page
    utils._inject_views_into_page(_page)

    return tk.render('ckanext_pages/%s.html' % page_type)


class PageEdit(MethodView):
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
            return base.abort(403, _(u'Unauthorized to Add/update Pages'))
        return context


    def post(self, id=None) -> Union[Response, str]:
        context = self._prepare()

        data_dict = _clean_dict(
            dict_fns.unflatten(
                _tuplize_dict(_parse_params(tk.request.form))))
        
        data_dict.update(
            _clean_dict(dict_fns.unflatten(
                    _tuplize_dict(_parse_params(tk.request.files))
                    )))


        try:
            if request.endpoint == 'pages.edit':
                data_dict.update({'id': id})

            link_data = tk.get_action('ckanext_pages_edit')(context, data_dict)

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)

        url = 'pages.pages_index'
        return h.redirect_to(url)


    def get(self, id=None, data: Optional[dict[str, Any]] = None,
            errors: Optional[dict[str, Any]] = None,
            error_summary: Optional[dict[str, Any]] = None) -> str:

        context = self._prepare()
        
        data = data or _clean_dict(
            dict_fns.unflatten(
                _tuplize_dict(
                    _parse_params(request.args, ignore_keys=CACHE_PARAMETERS)
                )
            )
        )

        previous_data = tk.get_action('ckanext_pages_show')(context, {'id': id}) if request.endpoint == 'pages.edit' else {}

        data = {**previous_data, **data}


        errors = errors or {}
        error_summary = error_summary or {}

        errors_json = h.dump_json(errors)

        return base.render(
            'ckanext_pages/page_edit.html', 
            extra_vars={
                u'errors_json': errors_json,
                u'data': data,
                u'errors': errors,
                u'error_summary': error_summary,
                u'action': 'new' if not id else 'edit',
            }
        )


class PageDelete(MethodView):
    def _prepare(self) -> Context:
        if 'cancel' in tk.request.args:
            tk.redirect_to('pages.pages_index')
    
        context = cast(Context, {
            u'model': model,
            u'session': model.Session,
            u'user': current_user.name,
            u'auth_user_obj': current_user,
        })

        try:
            tk.check_access(u'is_content_editor', context)
        except tk.NotAuthorized:
            return base.abort(403, _(u'Unauthorized to delete the Page'))
        return context


    def post(self, id) -> Union[Response, str]:
        context = self._prepare()

        data_dict = _clean_dict(
            dict_fns.unflatten(
                _tuplize_dict(_parse_params(tk.request.form))))

        try:
            link_data = tk.get_action('ckanext_pages_delete')(context, {'id': id})
            h.flash_success(_('Page deleted successfully!'))

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)

        url = 'pages.pages_index'
        return h.redirect_to(url)


    def get(self, id, data: Optional[dict[str, Any]] = None,
            errors: Optional[dict[str, Any]] = None,
            error_summary: Optional[dict[str, Any]] = None) -> str:

        context = self._prepare()
        
        data = data or _clean_dict(
            dict_fns.unflatten(
                _tuplize_dict(
                    _parse_params(request.args, ignore_keys=CACHE_PARAMETERS)
                )
            )
        )
        try:
            item = tk.get_action('ckanext_pages_show')(context, {'id': id})
        except tk.ObjectNotFound:
            # Page not found
            return tk.abort(404, _('Page not found'))
        
        data = {**item, **data}

        errors = errors or {}
        error_summary = error_summary or {}

        errors_json = h.dump_json(errors)

        return base.render(
            'ckanext_pages/confirm_delete.html', 
            extra_vars={
                u'errors_json': errors_json,
                u'data': data,
                u'item': item,
                u'type': 'page',
                u'errors': errors,
                u'error_summary': error_summary,
            }
        )



def register_pages(pages):
    pages.add_url_rule("/pages", view_func=index, endpoint="pages_index", methods=['GET'])
    pages.add_url_rule("/pages/<id>", view_func=show)

    pages.add_url_rule("/pages/edit/", view_func=PageEdit.as_view('new'), endpoint='new')
    pages.add_url_rule("/pages/edit/<id>", view_func=PageEdit.as_view('edit'), endpoint='edit')


    pages.add_url_rule('/pages/delete/<id>', view_func=PageDelete.as_view('pages_delete'), endpoint='pages_delete')

