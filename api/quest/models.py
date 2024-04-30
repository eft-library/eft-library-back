from database import DataBaseConnector
from sqlalchemy import Column, String, Integer, TIMESTAMP, ARRAY, Boolean, TEXT


class NPC(DataBaseConnector.Base):
    """
    NPC
    """
    __tablename__ = "tkw_npc_info"

    npc_id = Column(String, primary_key=True)
    npc_name_en = Column(String)
    npc_name_kr = Column(String)
    npc_img_path = Column(String)
    npc_order = Column(Integer)
    npc_update_time = Column(TIMESTAMP)


class QuestPreview(DataBaseConnector.Base):
    """
    QuestPreview
    """
    __tablename__ = "tkw_quest_info"

    quest_id = Column(Integer, primary_key=True)
    quest_npc_value = Column(String)
    quest_name_en = Column(String)
    quest_name_kr = Column(String)
    quest_objectives_en = Column(ARRAY(String))
    quest_objectives_kr = Column(ARRAY(String))
    quest_rewards_en = Column(ARRAY(String))
    quest_rewards_kr = Column(ARRAY(String))
    quest_required_kappa = Column(Boolean)
    quest_update_time = Column(TIMESTAMP)
    quest_order = Column(Integer)
    quest_guide = Column(TEXT)
