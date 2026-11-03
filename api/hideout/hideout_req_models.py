from typing import List

from pydantic import BaseModel


class CompleteHideoutStation(BaseModel):
    complete_list: List[str]


class ItemType(BaseModel):
    id: str
    count: int
    found_in_raid: bool


class UpdateStationItemRequest(BaseModel):
    user_item_list: List[ItemType]
