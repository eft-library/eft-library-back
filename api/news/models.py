from sqlalchemy import Column, String, TIMESTAMP
from database import DataBaseConnector


class Youtube(DataBaseConnector.Base):
    """
    Tarkov Youtube
    """

    __tablename__ = "tkl_youtube"

    id = Column(String, primary_key=True)
    update_time = Column(TIMESTAMP)
