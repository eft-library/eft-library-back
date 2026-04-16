from sqlalchemy import Column, INTEGER, TIMESTAMP, TEXT
from database import V3Database


class WipeV3(V3Database.Base):
    __tablename__ = "wipe"

    id = Column(INTEGER, primary_key=True)
    patch_version = Column(TEXT)
    season_start = Column(TEXT)
    season_end = Column(TEXT)
    create_time = Column(TIMESTAMP)


class InformationV3(V3Database.Base):
    __tablename__ = "information"

    id = Column(TEXT, primary_key=True)
    information_type = Column(TEXT)
    title_en = Column(TEXT)
    title_ko = Column(TEXT)
    title_ja = Column(TEXT)
    content_en = Column(TEXT)
    content_ko = Column(TEXT)
    content_ja = Column(TEXT)
    update_time = Column(TIMESTAMP)
