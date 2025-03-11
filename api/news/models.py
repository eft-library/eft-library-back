from sqlalchemy import Column, JSON, TIMESTAMP, TEXT, Boolean
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
    user_function = Column(JSON)


class Wipe(DataBaseConnector.Base):
    """
    wipe
    """

    __tablename__ = "tkl_wipe"

    id = Column("id", TEXT, primary_key=True)
    patch_version = Column(TEXT)
    season_start = Column(TEXT)
    season_end = Column(TEXT)
    create_time = Column(TIMESTAMP)

