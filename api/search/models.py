from sqlalchemy import Column, String, TIMESTAMP, INTEGER

from database import DataBaseConnector


class Search(DataBaseConnector.Base):
    """
    search info
    """

    __tablename__ = "tkl_search"

    value = Column(String, primary_key=True)
    link = Column(String)
    type = Column(String)
    page_value = Column(INTEGER)
    order = Column(INTEGER)
    update_time = Column(TIMESTAMP)
