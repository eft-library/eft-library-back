from database import DataBaseConnector
from sqlalchemy import Column, String, ARRAY, TEXT, TIMESTAMP, JSON, ForeignKey, Integer, NUMERIC
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import List


class PriceModel(DataBaseConnector.Base):
    """
    Price
    """

    __tablename__ = "tkl_item_price"

    id = Column(TEXT, primary_key=True)
    item_name_en = Column(String)
    item_name_kr = Column(String)
    item_image = Column(TEXT)
    trader = Column(JSON)
    category = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)
    history = relationship("PriceHistoryModel", backref="price", order_by="PriceHistoryModel.price_time")


class PriceHistoryModel(DataBaseConnector.Base):
    """
    Price History
    """

    __tablename__ = "tkl_item_price_history"

    id = Column(TEXT, ForeignKey("tkl_item_price.id"))
    item_price = Column("price", Integer)
    price_type = Column(String)
    price_time = Column(TIMESTAMP, primary_key=True)
    execute_time = Column(TIMESTAMP)


class PriceRankReq(BaseModel):
    """
    아이템 랭크 카테고리 파라미터
    """

    categoryList: List[str]