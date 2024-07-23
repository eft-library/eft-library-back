from database import DataBaseConnector
from sqlalchemy import (
    Column,
    Integer,
    TIMESTAMP,
    ARRAY,
    TEXT,
    Boolean,
)


class User(DataBaseConnector.Base):
    """
    User
    """

    __tablename__ = "tkl_user"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    email = Column(TEXT)
    image = Column(TEXT)
    nick_name = Column(TEXT)
    point = Column(Integer)
    is_ban = Column(Boolean)
    is_delete = Column(Boolean)
    grade = Column(TEXT)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    delete_time = Column(TIMESTAMP)


class UserQuest(DataBaseConnector.Base):
    """
    User quest
    """

    __tablename__ = "tkl_user_quest"

    user_email = Column(TEXT, primary_key=True)
    quest_id = Column(ARRAY(TEXT))
