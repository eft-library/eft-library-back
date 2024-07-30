from database import DataBaseConnector
from sqlalchemy import Column, Integer, TIMESTAMP, ARRAY, TEXT, Boolean, BIGINT


class ForumBoard(DataBaseConnector.Base):
    """
    Forum
    """

    __tablename__ = "tkl_forum"

    id = Column(BIGINT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    writer = Column(TEXT)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    view_count = Column(Integer)
    type = Column(TEXT)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)


class Issue(DataBaseConnector.Base):
    """
    Issue
    """

    __tablename__ = "tkl_issue"

    board_id = Column(BIGINT, primary_key=True)
    like_count = Column(Integer)
    writer = Column(TEXT)
    update_time = Column(TIMESTAMP)


class TipBoard(DataBaseConnector.Base):
    """
    Tip
    """

    __tablename__ = "tkl_tip"

    id = Column(BIGINT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    writer = Column(TEXT)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    view_count = Column(Integer)
    type = Column(TEXT)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)


class IncidentBoard(DataBaseConnector.Base):
    """
    Incident
    """

    __tablename__ = "tkl_incident"

    id = Column(BIGINT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    writer = Column(TEXT)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    view_count = Column(Integer)
    type = Column(TEXT)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)


class HumorBoard(DataBaseConnector.Base):
    """
    Humor
    """

    __tablename__ = "tkl_humor"

    id = Column(BIGINT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    writer = Column(TEXT)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    view_count = Column(Integer)
    type = Column(TEXT)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)


class NoticeBoard(DataBaseConnector.Base):
    """
    Notice
    """

    __tablename__ = "tkl_notice"

    id = Column(BIGINT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    writer = Column(TEXT)
    view_count = Column(Integer)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
