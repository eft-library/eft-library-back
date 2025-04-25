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

    __tablename__ = "npc_i18n"

    id = Column(TEXT, primary_key=True)
    name = Column(JSON)
    image = Column(String)
    order = Column(Integer)
    barter_info = Column(JSON)
    update_time = Column(TIMESTAMP)


class Quest(DataBaseConnector.Base):
    """
    Quest
    """

    __tablename__ = "quest_i18n"

    id = Column(String, primary_key=True)
    npc_id = Column(String, ForeignKey("npc_i18n.id"))
    url_mapping = Column(TEXT)
    name = Column(String)
    wiki_url = Column(TEXT)
    kappa_required = Column(Boolean)
    objectives = Column(JSON)
    finish_rewards = Column(JSON)
    min_player_level = Column(Integer)
    update_time = Column(TIMESTAMP)
    order = Column(Integer)
    guide = Column(JSON)
    task_next = Column(JSON)
    task_requirements = Column(JSON)
