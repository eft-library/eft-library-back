from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, ARRAY, TEXT

from database import DataBaseConnector


class Boss(DataBaseConnector.Base):
    """
    Boss
    """

    __tablename__ = "tkw_boss_info"

    boss_id = Column(Integer, primary_key=True)
    boss_name_en = Column(String)
    boss_name_kr = Column(String)
    boss_faction = Column(String)
    boss_location_spawn_chance_en = Column(JSON)
    boss_location_spawn_chance_kr = Column(JSON)
    boss_followers_en = Column(ARRAY(TEXT))
    boss_followers_kr = Column(ARRAY(TEXT))
    boss_img_path = Column(TEXT)
    boss_health_img_path = Column(ARRAY(TEXT))
    boss_health_total = Column(Integer)
    boss_location_guide = Column(TEXT)
    boss_loot = Column(ARRAY(TEXT))
    boss_spawn = Column(ARRAY(TEXT))
    boss_update_time = Column(TIMESTAMP)
