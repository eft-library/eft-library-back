from database import DataBaseConnector
from sqlalchemy import (
    Column,
    Integer,
    TIMESTAMP,
    ARRAY,
    TEXT,
    NUMERIC,
    Boolean,
    ForeignKey,
)
from pydantic import BaseModel
from typing import List


class UserQuestReq(BaseModel):
    """
    사용자 퀘스트 조회 요청
    """

    provider: str


class UserQuestAdd(BaseModel):
    """
    사용자 퀘스트 추가
    """

    provider: str
    quest_list: List[str]


class AddUserReq(BaseModel):
    """
    사용자 추가 시
    """

    id: str
    name: str
    email: str
    image: str


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


class UserQuest(DataBaseConnector.Base):
    """
    User quest
    """

    __tablename__ = "tkl_user_quest"

    user_email = Column(TEXT, primary_key=True)
    quest_id = Column(ARRAY(TEXT))
    is_clear = Column(Boolean)
