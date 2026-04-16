from sqlalchemy import Column, String, TIMESTAMP, INTEGER, NUMERIC
from database import V3Database


class AutocompleteItemV3(V3Database.Base):
    __tablename__ = "autocomplete_items"

    url = Column(String, primary_key=True)
    autocomplete_text_en = Column(String)
    autocomplete_text_ko = Column(String)
    autocomplete_text_ja = Column(String)
    category = Column(String)
    sort_order = Column(INTEGER)
    update_time = Column(TIMESTAMP)


class SitemapV3(V3Database.Base):
    __tablename__ = "sitemap"

    id = Column(INTEGER, primary_key=True)
    url = Column(String)
    priority = Column(NUMERIC)
    change_freq = Column(String)
    sitemap_value = Column(String)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
