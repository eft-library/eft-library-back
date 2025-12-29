from pydantic import BaseModel
from typing import List


class ProgressItemList(BaseModel):
    rebirthItemList: List[str]
    kappaItemList: List[str]
