from pydantic import BaseModel
from typing import List


class CompleteHideoutStation(BaseModel):
    """
    사용자 hideout station 건설
    """

    complete_list: List[str]


class BrokenHideoutStation(BaseModel):
    """
    사용자 hideout station 파괴
    """

    broken_id: str


class GetHideoutStation(BaseModel):
    """
    사용자 hideout station 조회
    """

    user_email: str


class ItemType(BaseModel):
    id: str
    count: int


class UpdateStationItemRequest(BaseModel):
    user_item_list: List[ItemType]
