from pydantic import BaseModel


class RebuildFront(BaseModel):
    rebuild_key: str
