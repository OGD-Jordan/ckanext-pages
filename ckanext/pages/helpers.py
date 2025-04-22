import ckan.lib.helpers as h
from ckan import model
from ckanext.pages.db import HeaderLogo, HeaderMainMenu, HeaderSecondaryMenu, MainPage
from sqlalchemy import case


def get_header_data():
    lang = h.lang()

    logo = HeaderLogo.Session.query(HeaderLogo).filter_by(is_visible=True).first()

    main_menu_items = (
        HeaderMainMenu.Session.query(HeaderMainMenu)
        .filter_by(is_visible=True).
        order_by(
            HeaderMainMenu.order,
            case(
                (HeaderMainMenu.menu_type == 'link', 0),
                (HeaderMainMenu.menu_type == 'menu', 1),
            ),
        )
        .all())

    secondary_menu_items = (
        HeaderSecondaryMenu.Session.query(HeaderSecondaryMenu)
        .filter_by(is_visible=True)
        .order_by(HeaderSecondaryMenu.order)
        .all()
    )

    def build_tree(items):
        menu = {item.id: item for item in items}
        for item in items:
            setattr(item, 'children', [])
        for item in items:
            if item.parent_id and item.parent_id in menu:
                menu[item.parent_id].children.append(item)
        return sorted(
            (item for item in items if not item.parent_id),
            key=lambda x: (x.order, 0 if getattr(x, 'menu_type', '') == 'link' else 1)
        )

    def sort_children(items):
        for item in items:
            item.children.sort(key=lambda x: (x.order, 0 if getattr(x, 'menu_type', '') == 'link' else 1))
            sort_children(item.children)

    main_menu_tree = build_tree(main_menu_items)
    secondary_menu_tree = build_tree(secondary_menu_items)

    sort_children(main_menu_tree)
    sort_children(secondary_menu_tree)

    return {
        'logo_url': logo.link if logo else '',
        'main_menu_tree': main_menu_tree,
        'secondary_menu_tree': secondary_menu_tree,
        'lang': lang,
    }

from ckan.common import _
import ckan.plugins.toolkit as tk

TARGET_VALUES_DICT = {
    '_self': _('Same Tab'),
    '_blank': _('New Tab'),
}

def get_helpers():
    return {
        'get_header_data': get_header_data,
        'target_display': target_display,
        'footer_column1_data': footer_column1_data,
        'footer_column_titles_data': footer_column_titles_data,
        'footer_column2_items': footer_column2_items,
        'footer_column3_items': footer_column3_items,
        'footer_social_items': footer_social_items,
        'footer_banner_items': footer_banner_items,
        'get_header_data': get_header_data,
        'get_main_page_all_sections': get_main_page_all_sections,
        'get_main_page_section': get_main_page_section,
    }



def target_display(value):
    return TARGET_VALUES_DICT.get(value, '')
    
def footer_column1_data():
    return tk.get_action('footer_main_show')({'ignore_auth': True}, {})

def footer_column_titles_data():
    return tk.get_action('footer_column_titles_show')({'ignore_auth': True}, {})

def footer_column2_items():
    return tk.get_action('footer_column_links_search')({'ignore_auth': True}, {'column_number': 2})

def footer_column3_items():
    return tk.get_action('footer_column_links_search')({'ignore_auth': True}, {'column_number': 3})

def footer_social_items():
    return tk.get_action('footer_social_media_items_search')({'ignore_auth': True}, {})

def footer_banner_items():
    return tk.get_action('footer_banner_item_list')({'ignore_auth': True}, {})


def get_main_page_all_sections():
    lang = h.lang()
    sections = MainPage.all()
    section_data = []
    for section in sections:
        section_data.append({
            'id': section.id,
            'title_1': section.main_title_1_ar if lang == 'ar' else section.main_title_1_en,
            'title_2': section.main_title_2_ar if lang == 'ar' else section.main_title_2_en,
            'brief': section.main_brief_ar if lang == 'ar' else section.main_brief_en
        })
    return section_data

def get_main_page_section(id):
    lang = h.lang()
    section = MainPage.get(id=id)
    return {
        'id': section.id,
        'title_1': section.main_title_1_ar if lang == 'ar' else section.main_title_1_en,
        'title_2': section.main_title_2_ar if lang == 'ar' else section.main_title_2_en,
        'brief': section.main_brief_ar if lang == 'ar' else section.main_brief_en
    }
