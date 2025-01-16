from pydantic import BaseModel
from typing import List


class UserQuestList(BaseModel):
    """
    사용자 퀘스트
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

class GetUserQuest(BaseModel):
    """
    사용자 퀘스트 정보 조회
    """

    user_email: str