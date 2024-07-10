from database import DataBaseConnector
from sqlalchemy import Column, Integer, TIMESTAMP, ARRAY, TEXT, NUMERIC
from pydantic import BaseModel


class Token(BaseModel):
    """
    사용자 관련 통신 시 사용할 token
    """

    token: str


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
