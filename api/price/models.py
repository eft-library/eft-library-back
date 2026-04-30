from database import V3Database
from sqlalchemy import (
    Column,
    TEXT,
    TIMESTAMP,
    Integer,
    NUMERIC,
    Boolean,
)
from pydantic import BaseModel
from typing import List


class ItemPriceV3(V3Database.Base):
    __tablename__ = "item_prices"

    item_id = Column(TEXT, primary_key=True)
    game_mode = Column(TEXT, primary_key=True)
    highest_trader_price = Column(NUMERIC)
    highest_trader_id = Column(TEXT)
    flea_market_price = Column(NUMERIC)
    trader_count = Column(Integer)
    has_flea = Column(Boolean)
    update_time = Column(TIMESTAMP)


class ItemTraderPriceV3(V3Database.Base):
    __tablename__ = "item_trader_prices"

    id = Column(TEXT, primary_key=True)
    item_id = Column(TEXT)
    game_mode = Column(TEXT)
    trader_id = Column(TEXT)
    price = Column(NUMERIC)


class ItemPriceHistoryV3(V3Database.Base):
    __tablename__ = "item_price_history"

    item_id = Column(TEXT, primary_key=True)
    game_mode = Column(TEXT, primary_key=True)
    price_time = Column(TIMESTAMP, primary_key=True)
    price = Column(Integer)


class PriceRankReqV3(BaseModel):
    """
    V3 아이템 랭크 카테고리 파라미터
    """

    categoryList: List[str]
