from pydantic import BaseModel
from typing import List


class UserQuestList(BaseModel):
    """
    사용자 퀘스트
    """

    userQuestList: List[str]
