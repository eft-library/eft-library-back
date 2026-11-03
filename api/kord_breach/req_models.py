from typing import List, Optional

from pydantic import BaseModel


class SaveKordBreachPreset(BaseModel):
    slotNo: int
    name: Optional[str] = None
    modifierIds: List[str]


class DeleteKordBreachPreset(BaseModel):
    slotNo: int
