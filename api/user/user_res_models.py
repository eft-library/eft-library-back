from database import DataBaseConnector
from sqlalchemy import (
    Column,
    Integer,
    TIMESTAMP,
    ARRAY,
    TEXT,
    Boolean,
    BIGINT,
    ForeignKey,
)
from sqlalchemy.orm import relationship


class User(DataBaseConnector.Base):
    """
    User
    """

    __tablename__ = "tkl_user"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    email = Column(TEXT)
    icon = Column(TEXT)
    nick_name = Column(TEXT)
    point = Column(BIGINT)
    is_admin = Column(Boolean)
    attendance_count = Column(Integer)
    create_time = Column(TIMESTAMP)
    attendance_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)


class UserGrade(DataBaseConnector.Base):
    """
    user grade
    """

    __tablename__ = "tkl_user_grade"

    max_point = Column(BIGINT, primary_key=True)
    min_point = Column(BIGINT)
    value = Column(TEXT)


class UserQuest(DataBaseConnector.Base):
    """
    User quest
    """

    __tablename__ = "tkl_user_quest"

    user_email = Column(TEXT, primary_key=True)
    quest_id = Column(ARRAY(TEXT))
