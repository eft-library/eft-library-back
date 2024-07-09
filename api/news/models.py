from sqlalchemy import Column, String, TIMESTAMP, TEXT
from database import DataBaseConnector


class News(DataBaseConnector.Base):
    """
    news
    """

    __tablename__ = "tkl_news"

    game_version = Column(TEXT, primary_key=True)
    arena_version = Column(TEXT)
    patch_link = Column(TEXT)
    event_link = Column(TEXT)
    youtube_id = Column(TEXT)
    next_update = Column(TEXT)
