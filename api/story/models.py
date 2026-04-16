from database import V3Database
from sqlalchemy import Column, TIMESTAMP, TEXT, JSON, INTEGER, NUMERIC


class StoryV3(V3Database.Base):
    __tablename__ = "story"

    id = Column(TEXT, primary_key=True)
    title_en = Column(TEXT)
    title_ko = Column(TEXT)
    title_ja = Column(TEXT)
    objectives_en = Column(TEXT)
    objectives_ko = Column(TEXT)
    objectives_ja = Column(TEXT)
    requirements_en = Column(TEXT)
    requirements_ko = Column(TEXT)
    requirements_ja = Column(TEXT)
    guide_en = Column(TEXT)
    guide_ja = Column(TEXT)
    guide_ko = Column(TEXT)
    sort_order = Column(INTEGER)
    update_time = Column(TIMESTAMP)


class StoryRoadmapV3(V3Database.Base):
    __tablename__ = "story_roadmap"

    id = Column(TEXT, primary_key=True)
    node_type = Column(TEXT)
    title_en = Column(TEXT)
    title_ko = Column(TEXT)
    title_ja = Column(TEXT)
    contents_en = Column(TEXT)
    contents_ko = Column(TEXT)
    contents_ja = Column(TEXT)
    desc_en = Column(TEXT)
    desc_ko = Column(TEXT)
    desc_ja = Column(TEXT)
    value_text = Column(TEXT)
    image = Column(TEXT)
    x_coordinate = Column(NUMERIC)
    y_coordinate = Column(NUMERIC)
    edge = Column(JSON)
    update_time = Column(TIMESTAMP)
