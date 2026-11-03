from sqlalchemy import BOOLEAN, INTEGER, TEXT, TIMESTAMP, Column

from database import Database


class User(Database.Base):
    __tablename__ = "user_info"

    email = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    nickname = Column(TEXT)
    is_admin = Column(BOOLEAN)
    attendance_count = Column(INTEGER)
    last_update_nickname = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP)
    attendance_time = Column(TIMESTAMP)


class UserReport(Database.Base):
    __tablename__ = "user_report"

    id = Column(INTEGER, primary_key=True)
    request_email = Column(TEXT)
    target_email = Column(TEXT)
    reason_type = Column(TEXT)
    reason = Column(TEXT)
    request_time = Column(TIMESTAMP)


class UserBlock(Database.Base):
    __tablename__ = "user_block"

    id = Column(INTEGER, primary_key=True)
    request_email = Column(TEXT)
    target_email = Column(TEXT)
    reason = Column(TEXT)
    create_time = Column(TIMESTAMP)


class UserPenalty(Database.Base):
    __tablename__ = "user_penalty"

    id = Column(INTEGER, primary_key=True)
    email = Column(TEXT)
    reason = Column(TEXT)
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
