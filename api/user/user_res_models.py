from sqlalchemy import ARRAY, BOOLEAN, INTEGER, TEXT, TIMESTAMP, Column

from database import V3Database


class UserV3(V3Database.Base):
    __tablename__ = "user_info"

    email = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    nickname = Column(TEXT)
    is_admin = Column(BOOLEAN)
    attendance_count = Column(INTEGER)
    last_update_nickname = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP)
    attendance_time = Column(TIMESTAMP)


class UserQuestV3(V3Database.Base):
    __tablename__ = "user_quest"

    email = Column(TEXT, primary_key=True)
    quest_list = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)


class UserReportV3(V3Database.Base):
    __tablename__ = "user_report"

    id = Column(INTEGER, primary_key=True)
    request_email = Column(TEXT)
    target_email = Column(TEXT)
    reason_type = Column(TEXT)
    reason = Column(TEXT)
    request_time = Column(TIMESTAMP)


class UserBlockV3(V3Database.Base):
    __tablename__ = "user_block"

    id = Column(INTEGER, primary_key=True)
    request_email = Column(TEXT)
    target_email = Column(TEXT)
    reason = Column(TEXT)
    create_time = Column(TIMESTAMP)


class UserPenaltyV3(V3Database.Base):
    __tablename__ = "user_penalty"

    id = Column(INTEGER, primary_key=True)
    email = Column(TEXT)
    reason = Column(TEXT)
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
