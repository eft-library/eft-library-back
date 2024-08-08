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
    is_delete_by_admin = Column(Boolean)
    is_delete_by_user = Column(Boolean)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    parent_user_email = Column(TEXT)
