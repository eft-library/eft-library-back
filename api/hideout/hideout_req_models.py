from typing import List

from pydantic import BaseModel


class CompleteHideoutStationV3(BaseModel):
    complete_list: List[str]


class ItemTypeV3(BaseModel):
    id: str
    count: int
    found_in_raid: bool


class UpdateStationItemRequestV3(BaseModel):
    user_item_list: List[ItemTypeV3]
