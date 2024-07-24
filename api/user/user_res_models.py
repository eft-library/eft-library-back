from database import DataBaseConnector
from sqlalchemy import Column, Integer, TIMESTAMP, ARRAY, TEXT, Boolean, BIGINT


class User(DataBaseConnector.Base):
    """
    User
    """

    __tablename__ = "tkl_user"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    email = Column(TEXT)
    image = Column(TEXT)
    image_list = Column(ARRAY(TEXT))
    nick_name = Column(TEXT)
    point = Column(BIGINT)
    is_ban = Column(Boolean)
    is_delete = Column(Boolean)
    is_admin = Column(Boolean)
    grade = Column(TEXT)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    ban_end_time = Column(TIMESTAMP)
    delete_time = Column(TIMESTAMP)


class UserQuest(DataBaseConnector.Base):
    """
    User quest
    """

    __tablename__ = "tkl_user_quest"

    user_email = Column(TEXT, primary_key=True)
    quest_id = Column(ARRAY(TEXT))
