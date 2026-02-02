from sqlalchemy import Column, String, TIMESTAMP, INTEGER

from database import DataBaseConnector


class Search(DataBaseConnector.Base):
    """
    search info
    """

    __tablename__ = "search_i18n"

    value = Column(String, primary_key=True)
    page_value = Column(String, primary_key=True)
    lang = Column(String, primary_key=True)
    link = Column(String)
    type = Column(String)
    order = Column(INTEGER)
    update_time = Column(TIMESTAMP)


class Sitemap(DataBaseConnector.Base):
    """
    sitemap.xml
    """

    __tablename__ = "sitemap"

    id = Column(INTEGER, primary_key=True)
    link = Column(String)
    priority = Column(INTEGER)
    value = Column(String)
    change_freq = Column(String)
    create_date = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
