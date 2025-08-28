from database import DataBaseConnector
from sqlalchemy import (
    Column,
    Integer,
    TIMESTAMP,
    TEXT,
    Boolean,
    INTEGER,
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


class UserReport(DataBaseConnector.Base):

    __tablename__ = "user_report"

    id = Column(INTEGER, primary_key=True)
    reporter_email = Column(TEXT)
    reported_email = Column(TEXT)
    reason_type = Column(TEXT)
    reason = Column(TEXT)
    create_time = Column(TIMESTAMP)
