from pydantic import BaseModel
from typing import List


class UserQuestDelete(BaseModel):
    """
    사용자 퀘스트 삭제시
    """

    userQuestList: List[str]


class UserQuestUpdate(BaseModel):
    """
    사용자 퀘스트 수정
    """

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

    nickname: str


class ChangeUserIcon(BaseModel):
    """
    사용자 아이콘 수정
    """

    icon: str
