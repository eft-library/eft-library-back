import httpx
import logging
import os
from api.chat.chat_req_models import ChatRequest
from api.chat.chat_res_models import ChatResponse, SourceDoc

log = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
MCP_CHAT_URL = f"{MCP_SERVER_URL}/api/rag/chat"


async def request_chat(req: ChatRequest) -> ChatResponse:
    payload = {
        "session_id": req.session_id,
        "query": req.query,
        "lang": req.lang,
        "source_table": None,  # 보낼 방법이 없음, 그냥 전체 검색
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            MCP_CHAT_URL,
            json=payload,
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()

    log.info(
        f"[chat_service] session={req.session_id} docs={len(data.get('docs', []))}"
    )

    return ChatResponse(
        answer=data["answer"],
        docs=[SourceDoc(**d) for d in data.get("docs", [])],
    )
