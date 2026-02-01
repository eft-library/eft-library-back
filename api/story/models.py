from database import DataBaseConnector
from sqlalchemy import Column, TIMESTAMP, TEXT, JSON, INTEGER


class Story(DataBaseConnector.Base):

    __tablename__ = "story_i18n"

    id = Column(TEXT, primary_key=True)
    name = Column(JSON)
    objectives = Column(JSON)
    rewards = Column(JSON)
    guide = Column(JSON)
    order = Column(INTEGER)
    update_time = Column(TIMESTAMP)
