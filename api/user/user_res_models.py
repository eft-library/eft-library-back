from database import DataBaseConnector
from sqlalchemy import (
    Column,
    Integer,
    TIMESTAMP,
    TEXT,
    Boolean,
)


class User(DataBaseConnector.Base):
    """
    User
    """

    __tablename__ = "user_info"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    nickname = Column(TEXT)
    email = Column(TEXT)
    is_admin = Column(Boolean)
    attendance_count = Column(Integer)
    last_update_nickname = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP)
    attendance_time = Column(TIMESTAMP)
