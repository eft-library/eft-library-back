from pydantic import BaseModel
from typing import List


class UserInfoReq(BaseModel):
    """
    사용자 정보 요청
    """

    provider: str


class UserQuestDelete(BaseModel):
    """
    사용자 퀘스트 삭제시
    """

    provider: str
    userQuestList: List[str]


class UserQuestReq(BaseModel):
    """
    사용자 퀘스트 조회 요청
    """

    provider: str


class UserQuestUpdate(BaseModel):
    """
    사용자 퀘스트 수정
    """

    provider: str
    userQuestList: List[str]


class AddUserReq(BaseModel):
    """
    사용자 추가 시
    """

    id: str
    name: str
    email: str
    image: str


class ChangeUserNickname(BaseModel):
    """
    사용자 닉네임 수정
    """

    provider: str
    nickname: str
