import httpx
import logging
import os
from api.chat.chat_req_models import ChatRequest
from api.chat.chat_res_models import ChatResponse, SourceDoc

log = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
MCP_CHAT_URL = f"{MCP_SERVER_URL}/api/rag/chat"
MCP_CHAT_STREAM_URL = f"{MCP_SERVER_URL}/api/rag/chat/stream"


async def request_chat(req: ChatRequest) -> ChatResponse:
    payload = {
        "session_id": req.session_id,
        "query": req.query,
        "lang": req.lang,
        "source_table": None,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(MCP_CHAT_URL, json=payload, timeout=120.0)
        resp.raise_for_status()
        data = resp.json()

    log.info(
        f"[chat_service] session={req.session_id} docs={len(data.get('docs', []))}"
    )
    return ChatResponse(
        answer=data["answer"],
        docs=[SourceDoc(**d) for d in data.get("docs", [])],
    )


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
