from typing import Dict, List
from pydantic import BaseModel
from .models import ThreeMapModel


class ThreeMapBase(BaseModel):
    three_map_id: str
    three_map_name_en : str
    three_map_name_kr : str
    three_map_path : str
    three_map_item_path : List[Dict[str, str]]


class ThreeMap(ThreeMapModel):
    three_map_id: str

    class Config:
        orm_mode = True
