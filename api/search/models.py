from sqlalchemy import Column, String, TIMESTAMP, INTEGER

from database import DataBaseConnector


class Search(DataBaseConnector.Base):
    """
    search info
    """

    __tablename__ = "tkl_search"

    value = Column(String, primary_key=True)
    link = Column(String)
    order = Column(INTEGER)
    page_value = Column(INTEGER)
    update_time = Column(TIMESTAMP)
