from sqlalchemy import Column, String, TIMESTAMP
from database import DataBaseConnector


class Youtube(DataBaseConnector.Base):
    """
    Tarkov Youtube
    """
    __tablename__ = "tkw_youtube"

    youtube_id = Column(String, primary_key=True)
    youtube_update_time = Column(TIMESTAMP)
