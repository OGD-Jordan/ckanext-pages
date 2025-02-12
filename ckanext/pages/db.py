import datetime
import os
import uuid
import json
from ckan.model import DomainObject
from six import text_type
import sqlalchemy as sa
from sqlalchemy import Column, types, ForeignKey
from sqlalchemy.orm import class_mapper
from ckan.model import Session
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect
from ckan.plugins.toolkit import BaseModel
import ckan.lib.helpers as h

import logging
import sqlalchemy as sa
from ckan.common import config

log = logging.getLogger(__name__)


try:
    from sqlalchemy.engine import Row
except ImportError:
    try:
        from sqlalchemy.engine.result import RowProxy as Row
    except ImportError:
        from sqlalchemy.engine.base import RowProxy as Row

from ckan import model
from ckan.model.domain_object import DomainObject

try:
    from ckan.plugins.toolkit import BaseModel
except ImportError:
    # CKAN <= 2.9
    from ckan.model.meta import metadata
    from sqlalchemy.ext.declarative import declarative_base

    BaseModel = declarative_base(metadata=metadata)

pages_table = None

def make_uuid():
    return text_type(uuid.uuid4())


class Page(DomainObject, BaseModel):
    __tablename__ = "ckanext_pages"

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    title_en = Column(types.UnicodeText, default=u'')
    title_ar = Column(types.UnicodeText, default=u'')
    name = Column(types.UnicodeText, default=u'', nullable=False)
    content_en = Column(types.UnicodeText, default=u'')
    content_ar = Column(types.UnicodeText, default=u'')
    image_url = Column(types.UnicodeText, default=u'')
    lang = Column(types.UnicodeText, default=u'')
    order = Column(types.UnicodeText, default=u'')
    private = Column(types.Boolean, default=True)
    group_id = Column(types.UnicodeText, default=None)
    user_id = Column(types.UnicodeText, default=u'')
    publish_date = Column(types.DateTime, nullable=True)  # Make it nullable
    page_type = Column(types.UnicodeText)
    created = Column(types.DateTime, default=datetime.datetime.utcnow)
    modified = Column(types.DateTime, default=datetime.datetime.utcnow)
    extras = Column(types.UnicodeText, default=u'{}')
    hidden = Column(types.Boolean, default=False)


    @classmethod
    def filter_custom(cls, **kwargs):
        q = cls.Session.query(cls)
        
        if kwargs:  
            q = q.filter_by(**kwargs)

        return q

    @classmethod
    def get(cls, id_or_name=None):
        return cls.filter_custom(id = id_or_name).first() or cls.filter_custom(name = id_or_name).first()


    @classmethod
    def pages(cls, **kw):
        '''Finds a single entity in the register.'''
        order = kw.pop('order', False)
        order_publish_date = kw.pop('order_publish_date', False)

        query = model.Session.query(cls).autoflush(False)
        query = query.filter_by(**kw)
        if order:
            query = query.order_by(sa.cast(cls.order, sa.Integer)).filter(cls.order != '')
        elif order_publish_date:
            query = query.order_by(cls.publish_date.desc()).filter(cls.publish_date != None)  # noqa: E711
        else:
            query = query.order_by(cls.created.desc())
        return query.all()

    def save(self):
        try:
            self.modified = datetime.datetime.utcnow()
            model.Session.add(self)
            model.Session.commit()
            print("Saved page with ID:", self.id)  # Debug: Confirm save
        except Exception as e:
            print("Error during saving:", str(e))  # Debug: Log errors
            raise e


class MainPage(DomainObject, BaseModel):
    __tablename__ = "main_page"

    id = Column(types.Integer, primary_key=True)
    main_title_1_ar = Column(types.UnicodeText, nullable=True)
    main_title_1_en = Column(types.UnicodeText, nullable=True)
    main_title_2_ar = Column(types.UnicodeText, nullable=True)
    main_title_2_en = Column(types.UnicodeText, nullable=True)
    main_brief_en = Column(types.UnicodeText, nullable=True)
    main_brief_ar = Column(types.UnicodeText, nullable=True)

    @classmethod
    def get(cls, **kw):
        query = cls.Session.query(cls).autoflush(False)
        return query.filter_by(**kw).first()

    @classmethod
    def all(cls):
        query = cls.Session.query(cls).order_by(cls.id).autoflush(False)
        return query.all()

class Event(DomainObject, BaseModel):
    __tablename__ = 'events'
    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    title_en = Column(types.UnicodeText, default=u'')
    title_ar = Column(types.UnicodeText, default=u'')
    name = Column(types.UnicodeText, default=u'', nullable=False)
    start_date = Column(types.DateTime, nullable=True)
    end_date = Column(types.DateTime, nullable=True)
    created = Column(types.DateTime, default=datetime.datetime.utcnow)
    brief_ar = Column(types.UnicodeText, nullable=True)
    brief_en = Column(types.UnicodeText, nullable=True)
    content_ar = Column(types.UnicodeText, default=u'')
    content_en = Column(types.UnicodeText, default=u'')
    image_url = Column(types.UnicodeText, default=u'')
    lang = Column(types.UnicodeText, default=u'')

    
    @classmethod
    def get(cls, id_or_name=None):
        if id_or_name:
            return cls.Session.query(cls).filter_by(id=id_or_name).first() or Session.query(cls).filter_by(name=id_or_name).first()
        return None

    @classmethod
    def events(cls, **kw):
        order = kw.pop('order', False)
        order_start_date = kw.pop('order_start_date', False)

        query = cls.Session.query(cls).autoflush(False)
        query = query.filter_by(**kw)
        if order:
            query = query.order_by(sa.cast(cls.order, sa.Integer)).filter(cls.order != '')
        elif order_start_date:
            query = query.order_by(cls.start_date.desc()).filter(cls.start_date != None)  # noqa: E711
        else:
            query = query.order_by(cls.created.desc())
        return query.all()

    def save(self):
        try:
            self.modified = datetime.datetime.utcnow()
            self.add(self)
            self.commit()
            print("Saved page with ID:", self.id)  # Debug: Confirm save
        except Exception as e:
            print("Error during saving:", str(e))  # Debug: Log errors
            raise e
    


class News(DomainObject, BaseModel):
    __tablename__ = 'news'
    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    title_en = Column(types.UnicodeText, default=u'')
    title_ar = Column(types.UnicodeText, default=u'')
    name = Column(types.UnicodeText, default=u'', nullable=False)
    news_date = Column(types.DateTime)
    brief_ar = Column(types.UnicodeText, nullable=True)
    brief_en = Column(types.UnicodeText, nullable=True)
    content_ar = Column(types.UnicodeText, default=u'')
    content_en = Column(types.UnicodeText, default=u'')
    image_url = Column(types.UnicodeText, default=u'')
    lang = Column(types.UnicodeText, default=u'') 
    created = Column(types.DateTime, default=datetime.datetime.utcnow)
    hidden = Column(types.Boolean, default=False)

    

    @classmethod
    def get(cls, id_or_name=None):
        if id_or_name:
            return cls.Session.query(cls).filter_by(id=id_or_name).first() or Session.query(cls).filter_by(name=id_or_name).first()
        return None

    @classmethod
    def news(cls, **kw):
        order = kw.pop('order', False)
        order_news_date = kw.pop('order_news_date', False)

        query = cls.Session.query(cls).autoflush(False)
        query = query.filter_by(**kw)
        if order:
            query = query.order_by(sa.cast(cls.order, sa.Integer)).filter(cls.order != '')
        elif order_news_date:
            query = query.order_by(cls.news_date.desc()).filter(cls.news_date != None)  # noqa: E711
        else:
            query = query.order_by(cls.created.desc())
        return query.all()

    def save(self):
        try:
            self.modified = datetime.datetime.utcnow()
            self.add(self)
            self.commit()
            print("Saved page with ID:", self.id)
        except Exception as e:
            print("Error during saving:", str(e))
            raise e


class HeaderLogo(DomainObject, BaseModel):
    __tablename__ = 'header_logo'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    logo_en = Column(types.UnicodeText, nullable=False)
    logo_ar = Column(types.UnicodeText, nullable=False)
    is_visible  = Column(types.Boolean, default=True)
    created = Column(types.DateTime, default=datetime.datetime.utcnow)
    modified = Column(types.DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def get(cls, session: Session):
        instance = session.query(cls).first()

        if not instance:
            instance = cls(
                logo_en="/images/mainlogo-en.png",
                logo_ar="/images/mainlogo-ar.png"
            )
            session.add(instance)
            session.commit()

        return instance

    @property
    def logo_en_filename(self):
        return self.logo_en.split('/')[-1]

    @property
    def logo_ar_filename(self):
        return self.logo_ar.split('/')[-1]

    @property
    def link(self):
        logo = getattr(self, f"logo_{h.lang()}")
        return logo if logo.startswith("/images/") else h.url_for_static(f"uploads/header_logos/{logo}", qualified=True)



class HeaderMainMenu(DomainObject, BaseModel):
    __tablename__ = 'header_main_menu'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    title_en = Column(types.UnicodeText, nullable=False)
    title_ar = Column(types.UnicodeText, nullable=False)
    link_en = Column(types.UnicodeText, nullable=False)
    link_ar = Column(types.UnicodeText, nullable=False)
    menu_type = Column(types.UnicodeText, nullable=False)  # Type: link/menu
    parent_id = Column(types.UnicodeText, ForeignKey('header_main_menu.id'))  # Recursive relationship
    order = Column(types.Integer, default=0)
    is_visible = Column(types.Boolean, default=True)
    created = Column(types.DateTime, default=datetime.datetime.utcnow)
    modified = Column(types.DateTime, default=datetime.datetime.utcnow)
    parent = relationship("HeaderMainMenu", remote_side=[id], backref="children")

    @classmethod
    def get_all(cls):
        return Session.query(cls).order_by(cls.order).all()

    @classmethod
    def toggle_visibility(cls, id):
        menu_item = Session.query(cls).get(id)
        if menu_item:
            menu_item.is_visible = not menu_item.is_visible
            menu_item.save()
            return menu_item
        return None


class HeaderSecondaryMenu(DomainObject, BaseModel):
    __tablename__ = 'header_secondary_menu'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    title_en = Column(types.UnicodeText, nullable=False)
    title_ar = Column(types.UnicodeText, nullable=False)
    link_en = Column(types.UnicodeText, nullable=False)
    link_ar = Column(types.UnicodeText, nullable=False)
    menu_type = Column(types.UnicodeText, nullable=False)  # Type: link/menu
    parent_id = Column(types.UnicodeText, ForeignKey('header_secondary_menu.id'))  # Recursive relationship
    order = Column(types.Integer, default=0)
    is_visible = Column(types.Boolean, default=True)
    created = Column(types.DateTime, default=datetime.datetime.utcnow)
    modified = Column(types.DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def toggle_visibility(cls, id):
        menu_item = Session.query(cls).get(id)
        if menu_item:
            menu_item.is_visible = not menu_item.is_visible
            menu_item.save()
            return menu_item
        return None

def table_dictize(obj, context, **kw):
    '''Get any model object and represent it as a dict'''
    result_dict = {}

    if isinstance(obj, Row):
        fields = obj.keys()
    else:
        ModelClass = obj.__class__
        table = class_mapper(ModelClass).mapped_table
        fields = [field.name for field in table.c]

    for field in fields:
        name = field
        if name in ('current', 'expired_timestamp', 'expired_id'):
            continue
        if name == 'continuity_id':
            continue
        value = getattr(obj, name)
        if name == 'extras' and value:
            result_dict.update(json.loads(value))
        elif value is None:
            result_dict[name] = value
        elif isinstance(value, dict):
            result_dict[name] = value
        elif isinstance(value, int):
            result_dict[name] = value
        elif isinstance(value, datetime.datetime):
            result_dict[name] = value.isoformat()
        elif isinstance(value, list):
            result_dict[name] = value
        else:
            result_dict[name] = text_type(value)

    result_dict.update(kw)

    context['metadata_modified'] = max(result_dict.get('revision_timestamp', ''),
                                       context.get('metadata_modified', ''))

    return result_dict


try:
    import ckan.plugins.toolkit as tk
    engine = sa.create_engine(tk.config.get('sqlalchemy.url'))

    Session = sessionmaker(bind=engine)()
    BaseModel.metadata.create_all(engine)
except Exception as e:
    log.error(str(e))

def setup():
    inspector = inspect(engine)
    table_names = [
        'ckanext_pages', 
        'header_secondary_menu', 
        'header_main_menu', 
        'header_logo', 
        'news', 
        'events',
        'main_page',
        "cms_footer_column_titles",
        "cms_footer_column_links",
        "cms_footer_social_media",
        "cms_footer_banner",
        "cms_footer_main",
        ]
    
    for tn in table_names:
        if not inspector.has_table(tn):
            BaseModel.metadata.tables[tn].create(engine)
            log.debug('%s table created' %tn)
        else:
            log.debug('%s table already exists' %tn)



def teardown():
    inspector = inspect(engine)
    table_names = [
        'ckanext_pages', 
        'header_secondary_menu', 
        'header_main_menu', 
        'header_logo', 
        'news', 
        'events',
        'main_page',
        "cms_footer_column_titles",
        "cms_footer_column_links",
        "cms_footer_social_media",
        "cms_footer_banner",
        "cms_footer_main",
        ]
    
    for tn in table_names:
        if inspector.has_table(tn):
            table = BaseModel.metadata.tables.get(tn)
            if table is not None:
                table.drop(engine)
                log.debug('%s table dropped' %tn)
            else:
                log.error('%s table not found in metadata' %tn)
        else:
            log.debug('%s table does not exist' %tn)


