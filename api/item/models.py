from sqlalchemy import Column, TEXT, TIMESTAMP, ARRAY, INTEGER, NUMERIC

from database import DataBaseConnector


class Headset(DataBaseConnector.Base):
    """
    Headset
    """
    __tablename__ = "tkw_head_phone"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
    update_time = Column(TIMESTAMP)


class HeadWear(DataBaseConnector.Base):
    """
    HeadWear
    """
    __tablename__ = "tkw_head_wear"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    class_value = Column(TEXT)
    areas_en = Column(ARRAY(TEXT))
    areas_kr = Column(ARRAY(TEXT))
    durability = Column(INTEGER)
    ricochet_chance = Column(NUMERIC)
    weight = Column(NUMERIC)
    image = Column(TEXT)
    update_time = Column(TIMESTAMP)
