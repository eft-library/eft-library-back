from pydantic import BaseModel
from typing import List


class ProgressItemList(BaseModel):
    userRebirth: List[str]
    userKappa: List[str]
