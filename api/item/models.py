from sqlalchemy import Column, TEXT, TIMESTAMP, JSON, ARRAY, INTEGER, NUMERIC, Integer
from database import DataBaseConnector


class Item(DataBaseConnector.Base):
    """
    Item
    """

    __tablename__ = "tkl_item"

    id = Column(TEXT, primary_key=True)
    name_en = Column(TEXT)
    name_kr = Column(TEXT)
    category = Column(TEXT)
    image = Column(TEXT)
    info = Column(JSON)
    image_width = Column(NUMERIC)
    image_height = Column(NUMERIC)
    url_mapping = Column(TEXT)
    update_time = Column(TIMESTAMP)
