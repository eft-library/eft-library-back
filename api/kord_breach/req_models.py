from typing import List, Optional

from pydantic import BaseModel


class SaveKordBreachPresetV3(BaseModel):
    slotNo: int
    name: Optional[str] = None
    modifierIds: List[str]


class DeleteKordBreachPresetV3(BaseModel):
    slotNo: int
