from database import DataBaseConnector
from sqlalchemy import Column, Integer, TIMESTAMP, ARRAY, TEXT, Boolean, BIGINT


class ForumBoard(DataBaseConnector.Base):
    """
    Forum
    """

    __tablename__ = "tkl_board_forum"

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


class TipBoard(DataBaseConnector.Base):
    """
    Tip
    """

    __tablename__ = "tkl_board_tip"

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


class PvpBoard(DataBaseConnector.Base):
    """
    Pvp
    """

    __tablename__ = "tkl_board_pvp"

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


class PveBoard(DataBaseConnector.Base):
    """
    Pve
    """

    __tablename__ = "tkl_board_pve"

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


class ArenaBoard(DataBaseConnector.Base):
    """
    Arena
    """

    __tablename__ = "tkl_board_arena"

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


class QuestionBoard(DataBaseConnector.Base):
    """
    Question
    """

    __tablename__ = "tkl_board_question"

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


class PostLike(DataBaseConnector.Base):
    """
    Post like
    """

    __tablename__ = "tkl_post_like"

    board_id = Column(BIGINT, primary_key=True)
    user_email = Column(TEXT, primary_key=True)
    update_time = Column(TIMESTAMP)


class Issue(DataBaseConnector.Base):
    """
    Issue
    """

    __tablename__ = "tkl_issue"

    board_id = Column(BIGINT, primary_key=True)
    writer = Column(TEXT)
    update_time = Column(TIMESTAMP)


class BoardType(DataBaseConnector.Base):
    """
    Board Type
    """

    __tablename__ = "tkl_board_type"

    id = Column(TEXT, primary_key=True)
    name_en = Column(TEXT)
    name_kr = Column(TEXT)
    order = Column(Integer)
    value = Column(TEXT)
