from database import DataBaseConnector
from sqlalchemy import (
    Column,
    String,
    ARRAY,
    TEXT,
    TIMESTAMP
)

class Event(DataBaseConnector.Base):
    """
    Event
    """

    __tablename__ = "tkl_event"

    id = Column("id", TEXT, primary_key=True)
    name_en = Column(String)
    name_kr = Column(String)
    event_text_en = Column(ARRAY(TEXT))
    event_text_kr = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)
