from database import DataBaseConnector
from sqlalchemy import Column, String, Integer, TIMESTAMP, ARRAY, Boolean, TEXT


class NPC(DataBaseConnector.Base):
    """
    NPC
    """
    __tablename__ = "tkw_npc_info"

    id = Column(String, primary_key=True)
    name_en = Column(String)
    name_kr = Column(String)
    img_path = Column(String)
    order = Column(Integer)
    update_time = Column(TIMESTAMP)


class QuestPreview(DataBaseConnector.Base):
    """
    QuestPreview
    """
    __tablename__ = "tkw_quest"

    id = Column(Integer, primary_key=True)
    npc_value = Column(String)
    name_en = Column(String)
    name_kr = Column(String)
    objectives_en = Column(ARRAY(String))
    objectives_kr = Column(ARRAY(String))
    rewards_en = Column(ARRAY(String))
    rewards_kr = Column(ARRAY(String))
    required_kappa = Column(Boolean)
    update_time = Column(TIMESTAMP)
    order = Column(Integer)
    guide = Column(TEXT)
