from database import V3Database
from sqlalchemy import (
    Column,
    Computed,
    TEXT,
    TIMESTAMP,
    Integer,
    NUMERIC,
    Boolean,
)
from pydantic import BaseModel
from typing import List, Optional


class PriceSeasonV3(V3Database.Base):
    __tablename__ = "price_seasons"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    starts_at = Column(TIMESTAMP(timezone=True))
    ends_at = Column(TIMESTAMP(timezone=True))
    is_current = Column(Boolean, nullable=False)
    collected_at = Column(TIMESTAMP(timezone=True), nullable=False)
    update_time = Column(TIMESTAMP(timezone=True), nullable=False)


class ItemPriceV3(V3Database.Base):
    __tablename__ = "item_prices"

    item_id = Column(TEXT, primary_key=True)
    game_mode = Column(TEXT, primary_key=True)
    season_id = Column(TEXT)
    season_key = Column(
        TEXT, Computed("coalesce(season_id, '')", persisted=True), primary_key=True
    )
    highest_trader_price = Column(NUMERIC)
    highest_trader_id = Column(TEXT)
    flea_market_price = Column(NUMERIC)
    trader_count = Column(Integer)
    has_flea = Column(Boolean)
    update_time = Column(TIMESTAMP)


class ItemTraderPriceV3(V3Database.Base):
    __tablename__ = "item_trader_prices"

    id = Column(TEXT, nullable=False)
    item_id = Column(TEXT, primary_key=True)
    game_mode = Column(TEXT, primary_key=True)
    season_id = Column(TEXT)
    season_key = Column(
        TEXT, Computed("coalesce(season_id, '')", persisted=True), primary_key=True
    )
    trader_id = Column(TEXT, primary_key=True)
    price = Column(NUMERIC)


class ItemPriceHistoryV3(V3Database.Base):
    __tablename__ = "item_price_history"

    item_id = Column(TEXT, primary_key=True)
    game_mode = Column(TEXT, primary_key=True)
    season_id = Column(TEXT)
    season_key = Column(
        TEXT, Computed("coalesce(season_id, '')", persisted=True), primary_key=True
    )
    price_time = Column(TIMESTAMP, primary_key=True)
    price = Column(Integer)


class PriceRankReqV3(BaseModel):
    """
    V3 아이템 랭크 카테고리 파라미터
    """

    categoryList: List[str]
    seasonId: Optional[str] = None
