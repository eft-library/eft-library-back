from sqlalchemy import Column, TEXT, JSON, NUMERIC
from database import DataBaseConnector


class ItemFleaSummary(DataBaseConnector.Base):

    __tablename__ = "item_flea_summary"

    id = Column(TEXT, primary_key=True)
    name = Column(JSON)
    image = Column(TEXT)
    category = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    flea_market_price = Column(NUMERIC)
