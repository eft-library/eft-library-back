from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, TEXT
from sqlalchemy.dialects.postgresql import ARRAY

from database import DataBaseConnector


class Boss(DataBaseConnector.Base):
    """
    Boss
    """

    __tablename__ = "tkw_boss"

    id = Column(Integer, primary_key=True)
    name_en = Column(String)
    name_kr = Column(String)
    faction = Column(String)
    location_spawn_chance_en = Column(JSON)
    location_spawn_chance_kr = Column(JSON)
    followers_en = Column(ARRAY(TEXT))
    followers_kr = Column(ARRAY(TEXT))
    img_path = Column(TEXT)
    health_img_path = Column(ARRAY(TEXT))
    health_total = Column(Integer)
    location_guide = Column(TEXT)
    loot = Column(ARRAY(TEXT))
    spawn = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)
