from database import DataBaseConnector
from sqlalchemy import (
    Column,
    Integer,
    TIMESTAMP,
    ARRAY,
    TEXT,
    Boolean,
    BIGINT,
)


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
    grade = Column(Integer)
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

    id = Column(Integer, primary_key=True)
    score = Column(BIGINT)
    value = Column(TEXT)


class UserIcon(DataBaseConnector.Base):
    """
    user icon
    """

    __tablename__ = "tkl_user_icon"

    user_email = Column(TEXT, primary_key=True)
    icon_list = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)


class UserBan(DataBaseConnector.Base):
    """
    user ban
    """

    __tablename__ = "tkl_user_ban"

    user_email = Column(TEXT, primary_key=True)
    admin_email = Column(TEXT)
    ban_reason = Column(TEXT)
    ban_start_time = Column(TIMESTAMP)
    ban_end_time = Column(TIMESTAMP)


class UserDelete(DataBaseConnector.Base):
    """
    user delete
    """

    __tablename__ = "tkl_user_delete"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    email = Column(TEXT)
    icon = Column(TEXT)
    nick_name = Column(TEXT)
    point = Column(BIGINT)
    grade = Column(Integer)
    is_admin = Column(Boolean)
    attendance_count = Column(Integer)
    create_time = Column(TIMESTAMP)
    attendance_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    delete_end_time = Column(TIMESTAMP)


class UserQuest(DataBaseConnector.Base):
    """
    User quest
    """

    __tablename__ = "tkl_user_quest"

    user_email = Column(TEXT, primary_key=True)
    quest_id = Column(ARRAY(TEXT))


class UserPostStatistics(DataBaseConnector.Base):
    """
    User post statistics
    """

    __tablename__ = "tkl_user_post_statistics"

    user_email = Column(TEXT, primary_key=True)
    post_count = Column(BIGINT)
    comment_count = Column(BIGINT)
