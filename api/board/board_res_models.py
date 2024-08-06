from database import DataBaseConnector
from sqlalchemy import Column, Integer, TIMESTAMP, TEXT, ForeignKey
from sqlalchemy.orm import relationship


class ForumBoard(DataBaseConnector.Base):
    """
    Forum
    """

    __tablename__ = "tkl_board_forum"

    id = Column(TEXT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    writer = Column(TEXT)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    view_count = Column(Integer)
    type = Column(TEXT, ForeignKey("tkl_board_type.value"))
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    type_kr = relationship("BoardType", backref="forum")


class TipBoard(DataBaseConnector.Base):
    """
    Tip
    """

    __tablename__ = "tkl_board_tip"

    id = Column(TEXT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    writer = Column(TEXT)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    view_count = Column(Integer)
    type = Column(TEXT, ForeignKey("tkl_board_type.value"))
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    type_kr = relationship("BoardType", backref="tip")


class PvpBoard(DataBaseConnector.Base):
    """
    Pvp
    """

    __tablename__ = "tkl_board_pvp"

    id = Column(TEXT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    writer = Column(TEXT)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    view_count = Column(Integer)
    type = Column(TEXT, ForeignKey("tkl_board_type.value"))
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    type_kr = relationship("BoardType", backref="pvp")


class PveBoard(DataBaseConnector.Base):
    """
    Pve
    """

    __tablename__ = "tkl_board_pve"

    id = Column(TEXT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    writer = Column(TEXT)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    view_count = Column(Integer)
    type = Column(TEXT, ForeignKey("tkl_board_type.value"))
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    type_kr = relationship("BoardType", backref="pve")


class ArenaBoard(DataBaseConnector.Base):
    """
    Arena
    """

    __tablename__ = "tkl_board_arena"

    id = Column(TEXT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    writer = Column(TEXT)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    view_count = Column(Integer)
    type = Column(TEXT, ForeignKey("tkl_board_type.value"))
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    type_kr = relationship("BoardType", backref="arena")


class QuestionBoard(DataBaseConnector.Base):
    """
    Question
    """

    __tablename__ = "tkl_board_question"

    id = Column(TEXT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    writer = Column(TEXT)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    view_count = Column(Integer)
    type = Column(TEXT, ForeignKey("tkl_board_type.value"))
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    type_kr = relationship("BoardType", backref="question")


class NoticeBoard(DataBaseConnector.Base):
    """
    Notice
    """

    __tablename__ = "tkl_board_notice"

    id = Column(TEXT, primary_key=True)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    writer = Column(TEXT)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    view_count = Column(Integer)
    type = Column(TEXT, ForeignKey("tkl_board_type.value"))
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    type_kr = relationship("BoardType", backref="notice")


class PostLike(DataBaseConnector.Base):
    """
    Post like
    """

    __tablename__ = "tkl_post_like"

    board_id = Column(TEXT, primary_key=True)
    user_email = Column(TEXT, primary_key=True)
    update_time = Column(TIMESTAMP)


class PostDisLike(DataBaseConnector.Base):
    """
    Post Dislike
    """

    __tablename__ = "tkl_post_dislike"

    board_id = Column(TEXT, primary_key=True)
    user_email = Column(TEXT, primary_key=True)
    update_time = Column(TIMESTAMP)


class Issue(DataBaseConnector.Base):
    """
    Issue
    """

    __tablename__ = "tkl_board_issue"

    board_id = Column(TEXT, primary_key=True)
    board_type = Column(TEXT)
    create_time = Column(TIMESTAMP)


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
