from sqlalchemy import Column, String, TIMESTAMP, INTEGER

from database import DataBaseConnector


class Search(DataBaseConnector.Base):
    """
    search info
    """

    __tablename__ = "tkl_search"

    id = Column(String, primary_key=True)
    value = Column(String)
    link = Column(String)
    order = Column(INTEGER)
    update_time = Column(TIMESTAMP)
