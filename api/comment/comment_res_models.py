from database import DataBaseConnector
from sqlalchemy import (
    Column,
    Integer,
    TIMESTAMP,
    TEXT,
    Boolean,
)


class Comments(DataBaseConnector.Base):
    """
    Comment
    """

    __tablename__ = "tkl_comments"

    id = Column(TEXT, primary_key=True)
    board_id = Column(TEXT)
    user_email = Column(TEXT)
    board_type = Column(TEXT)
    parent_id = Column(TEXT)
    contents = Column(TEXT)
    depth = Column(Integer)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    is_delete_by_admin = Column(Boolean)
    is_delete_by_user = Column(Boolean)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    parent_user_email = Column(TEXT)


class CommentLike(DataBaseConnector.Base):
    """
    Comment like
    """

    __tablename__ = "tkl_comment_like"

    comment_id = Column(TEXT, primary_key=True)
    user_email = Column(TEXT, primary_key=True)
    update_time = Column(TIMESTAMP)


class CommentDisLike(DataBaseConnector.Base):
    """
    Comment Dislike
    """

    __tablename__ = "tkl_comment_dislike"

    comment_id = Column(TEXT, primary_key=True)
    user_email = Column(TEXT, primary_key=True)
    update_time = Column(TIMESTAMP)


class CommentReport(DataBaseConnector.Base):
    """
    Comment report
    """

    __tablename__ = "tkl_comment_report"

    comment_id = Column(TEXT, primary_key=True)
    report_user = Column(TEXT)
    report_reason = Column(TEXT)
    create_time = Column(TIMESTAMP)
