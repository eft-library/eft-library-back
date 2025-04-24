from database import DataBaseConnector
from sqlalchemy import Column, TEXT, TIMESTAMP, JSON


class Event(DataBaseConnector.Base):
    """
    Event
    """

    __tablename__ = "event_i18n"

    id = Column(TEXT, primary_key=True)
    name = Column(JSON)
    description = Column(TEXT)
    update_time = Column(TIMESTAMP)
