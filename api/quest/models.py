from database import DataBaseConnector
from sqlalchemy import (
    Column,
    String,
    Integer,
    TIMESTAMP,
    ARRAY,
    Boolean,
    TEXT,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship


class NPC(DataBaseConnector.Base):
    """
    NPC
    """

    __tablename__ = "tkl_npc"

    id = Column(TEXT, primary_key=True)
    name_en = Column(TEXT)
    name_kr = Column(TEXT)
    image = Column(String)
    order = Column(Integer)
    update_time = Column(TIMESTAMP)


class QuestPreview(DataBaseConnector.Base):
    """
    QuestPreview
    """

    __tablename__ = "tkl_quest"

    id = Column(String, primary_key=True)
    npc_value = Column(String, ForeignKey("tkl_npc.id"))
    title_en = Column("name_en", String)
    title_kr = Column("name_kr", String)
    objectives_en = Column(ARRAY(String))
    objectives_kr = Column(ARRAY(String))
    rewards_en = Column(ARRAY(String))
    rewards_kr = Column(ARRAY(String))
    required_kappa = Column(Boolean)
    update_time = Column(TIMESTAMP)
    order = Column(Integer)
    guide = Column(TEXT)
    requires = Column(JSON)
    next = Column(JSON)
    is_event = Column(Boolean)
    sub = relationship("RelatedQuest", backref="quest_preview")


class RelatedQuest(DataBaseConnector.Base):
    """
    Related Quest
    """

    __tablename__ = "tkl_related_quest"

    item_id = Column(TEXT, primary_key=True)
    quest_id = Column(TEXT, ForeignKey("tkl_quest.id"))
    item_name_en = Column(TEXT)
    quest_name_en = Column(TEXT)
    item_name_kr = Column(TEXT)
    quest_name_kr = Column(TEXT)
    count = Column(Integer)
    type = Column(TEXT)
    in_raid = Column(Boolean)
    item_image = Column(TEXT)
    desc_text = Column(ARRAY(TEXT))
    item_link = Column(TEXT)

