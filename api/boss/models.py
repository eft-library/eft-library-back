from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, TEXT, ARRAY
from database import DataBaseConnector


class Boss(DataBaseConnector.Base):
    """
    Boss
    """

    __tablename__ = "boss_i18n"

    id = Column(TEXT, primary_key=True)
    name = Column(JSON)
    parent_id = Column(TEXT)
    faction = Column(String)
    image = Column(TEXT)
    health_total = Column(Integer)
    health_image = Column(TEXT)
    item_info = Column(JSON)
    spawn_chance = Column(JSON)
    spawn_map = Column(ARRAY(TEXT))
    location_guide = Column(JSON)
    order = Column(Integer)
    url_mapping = Column(TEXT)
    update_time = Column(TIMESTAMP)
