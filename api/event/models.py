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
)


class Event(DataBaseConnector.Base):
    """
    Event
    """

    __tablename__ = "tkl_event"

    id = Column(String, primary_key=True)
    npc_value = Column(String)
    title_en = Column("name_en", String)
    title_kr = Column("name_kr", String)
    objectives_en = Column(ARRAY(String))
    objectives_kr = Column(ARRAY(String))
    rewards_en = Column(ARRAY(String))
    rewards_kr = Column(ARRAY(String))
    required_kappa = Column(Boolean)
    order = Column(Integer)
    guide = Column(TEXT)
    requires = Column(JSON)
    next = Column(JSON)
    event_text_en = Column(ARRAY(String))
    event_text_kr = Column(ARRAY(String))
    update_time = Column(TIMESTAMP)
