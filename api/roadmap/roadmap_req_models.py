from pydantic import BaseModel
from typing import List


class SaveRoadmap(BaseModel):
    """
    사용자 roadmap 저장
    """

    questList: List[str]
