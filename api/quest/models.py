from database import DataBaseConnector
from sqlalchemy import Column, String, Integer, TIMESTAMP


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


