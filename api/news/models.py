from sqlalchemy import Column, TIMESTAMP, TEXT, JSON
from database import DataBaseConnector, V3Database


class Wipe(DataBaseConnector.Base):
    """
    wipe
    """

    __tablename__ = "wipe_i18n"

    id = Column("id", TEXT, primary_key=True)
    patch_version = Column(TEXT)
    season_start = Column(TEXT)
    season_end = Column(TEXT)
    create_time = Column(TIMESTAMP)


class Information(DataBaseConnector.Base):
    """
    Information
    """

    __tablename__ = "information_i18n"

    id = Column(TEXT, primary_key=True)
    type = Column(TEXT)
    name = Column(JSON)
    description = Column(TEXT)
    update_time = Column(TIMESTAMP)


class WipeV3(V3Database.Base):
    __tablename__ = "wipe"

    id = Column(TEXT, primary_key=True)
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
