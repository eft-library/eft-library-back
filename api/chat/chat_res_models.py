from pydantic import BaseModel


class SourceDoc(BaseModel):
    source_table: str
    source_id: str
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    docs: list[SourceDoc]
