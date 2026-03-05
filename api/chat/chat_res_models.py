from pydantic import BaseModel
from database import DataBaseConnector
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, Integer, Boolean, JSON


class SourceDoc(BaseModel):
    source_table: str
    source_id: str
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    docs: list[SourceDoc]


class RagSearch(DataBaseConnector.Base):
    """
    RagSearch
    """

    __tablename__ = "rag_search_i18n"

    value = Column(String, primary_key=True)
    lang = Column(String, primary_key=True)
    update_time = Column(TIMESTAMP)
