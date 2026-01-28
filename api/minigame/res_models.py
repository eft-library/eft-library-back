from database import DataBaseConnector
from sqlalchemy import Column, INTEGER, TEXT, BIGINT, JSON, NUMERIC
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP


class ItemFleaSummary(DataBaseConnector.Base):

    __tablename__ = "item_flea_summary"

    id = Column(TEXT, primary_key=True)
    name = Column(JSON)
    image = Column(TEXT)
    category = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    flea_market_price = Column(NUMERIC)


class UserMinigameScore(DataBaseConnector.Base):

    __tablename__ = "user_minigame_score"

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    nickname = Column(TEXT)
    game_type = Column(TEXT)
    score = Column(BIGINT)
    create_time = Column(TIMESTAMP(timezone=True), server_default=func.now())
