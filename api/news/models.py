from sqlalchemy import Column, TIMESTAMP, TEXT, JSON
from database import DataBaseConnector


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


class Event(DataBaseConnector.Base):
    """
    Event
    """

    __tablename__ = "event_i18n"

    id = Column(TEXT, primary_key=True)
    name = Column(JSON)
    description = Column(TEXT)
    update_time = Column(TIMESTAMP)


class Notice(DataBaseConnector.Base):
    """
    Notice
    """

    __tablename__ = "notice_i18n"

    id = Column("id", TEXT, primary_key=True)
    name = Column(JSON)
    description = Column(JSON)
    update_time = Column(TIMESTAMP)


class PatchNotes(DataBaseConnector.Base):
    """
    PatchNotes
    """

    __tablename__ = "patch_notes_i18n"

    id = Column("id", TEXT, primary_key=True)
    name = Column(JSON)
    description = Column(JSON)
    update_time = Column(TIMESTAMP)
