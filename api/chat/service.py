import httpx
import logging
import os
from api.chat.chat_req_models import ChatRequest
from api.chat.chat_res_models import RagSearch
from database import DataBaseConnector

log = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
MCP_CHAT_URL = f"{MCP_SERVER_URL}/api/rag/chat"
MCP_CHAT_STREAM_URL = f"{MCP_SERVER_URL}/api/rag/chat/stream"


def get_chat_search():
    try:
        with DataBaseConnector.SessionLocal() as s:
            search_list = s.query(RagSearch).all()
            return search_list
    except Exception as e:
        log.error(
            f"get_chat_search error: {e}",
            exc_info=True,
        )
        return None


async def request_chat_stream(req: ChatRequest):
    payload = {
        "session_id": req.session_id,
        "query": req.query,
        "lang": req.lang,
        "source_table": None,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", MCP_CHAT_STREAM_URL, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    yield f"{line}\n\n"
