from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    query: str
    lang: str = "ko"
    domain: str | None = None
    rag_limit: int | None = None
    history_limit: int | None = None
