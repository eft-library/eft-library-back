from sqlalchemy import Column, String, TIMESTAMP, INTEGER

from database import DataBaseConnector


class Search(DataBaseConnector.Base):
    """
    search info
    """

    __tablename__ = "tkw_search_info"

    search_id = Column(String, primary_key=True)
    search_value = Column(String)
    search_link = Column(String)
    search_order = Column(INTEGER)
    search_update_time = Column(TIMESTAMP)
