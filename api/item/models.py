from sqlalchemy import Column, TEXT, TIMESTAMP, JSON, NUMERIC
from database import DataBaseConnector


class Item(DataBaseConnector.Base):
    """
    Item
    """

    __tablename__ = "item_i18n"

    id = Column(TEXT, primary_key=True)
    name = Column(JSON)
    image_width = Column(NUMERIC)
    image_height = Column(NUMERIC)
    url_mapping = Column(TEXT)
    category = Column(TEXT)
    image = Column(TEXT)
    info = Column(JSON)
    update_time = Column(TIMESTAMP)
