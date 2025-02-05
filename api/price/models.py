from database import DataBaseConnector
from sqlalchemy import Column, String, ARRAY, TEXT, TIMESTAMP, JSON


class Price(DataBaseConnector.Base):
    """
    Price
    """

    __tablename__ = "tkl_item_price"

    id = Column("id", TEXT, primary_key=True)
    item_name_en = Column(String)
    item_name_kr = Column(String)
    item_image = Column(TEXT)
    trader = Column(JSON)
    update_time = Column(TIMESTAMP)
