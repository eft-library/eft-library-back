from database import DataBaseConnector
from sqlalchemy import Column, TIMESTAMP, TEXT, JSON, INTEGER, NUMERIC


class Story(DataBaseConnector.Base):

    __tablename__ = "story_i18n"

    id = Column(TEXT, primary_key=True)
    name = Column(JSON)
    objectives = Column(JSON)
    requirements = Column(JSON)
    guide = Column(JSON)
    order = Column(INTEGER)
    update_time = Column(TIMESTAMP)


class StoryRoadmap(DataBaseConnector.Base):

    __tablename__ = "story_roadmap_i18n"

    id = Column(TEXT, primary_key=True)
    story_id = Column(TEXT)
    node_type = Column(TEXT)
    title = Column(JSON)
    contents = Column(JSON)
    image = Column(JSON)
    x_coordinate = Column(NUMERIC)
    y_coordinate = Column(NUMERIC)
    edge = Column(JSON)
    node_meta = Column(JSON)
