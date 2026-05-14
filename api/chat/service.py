import httpx
import json
import logging
import os
from api.chat.chat_req_models import ChatRequest
from api.chat.chat_res_models import RagSearch
from database import DataBaseConnector

log = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
MCP_CHAT_STREAM_URL = f"{MCP_SERVER_URL}/api/rag/v3/chat/stream"


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
        "domain": req.domain,
    }
    if req.rag_limit is not None:
        payload["rag_limit"] = req.rag_limit
    if req.history_limit is not None:
        payload["history_limit"] = req.history_limit

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", MCP_CHAT_STREAM_URL, json=payload) as resp:
                if resp.status_code >= 400:
                    body = await resp.aread()
                    message = body.decode("utf-8", errors="replace")
                    log.error(
                        "MCP chat stream error status=%s body=%s",
                        resp.status_code,
                        message[:1000],
                    )
                    yield _sse_error(
                        f"Agent server returned HTTP {resp.status_code}",
                        message,
                    )
                    yield _sse_done()
                    return

                async for line in resp.aiter_lines():
                    if line:
                        yield f"{line}\n\n"
    except httpx.HTTPError as e:
        log.error("MCP chat stream connection error: %s", e, exc_info=True)
        yield _sse_error("Agent stream connection failed", str(e))
        yield _sse_done()
    except Exception as e:
        log.error("chat stream proxy error: %s", e, exc_info=True)
        yield _sse_error("Chat stream proxy failed", str(e))
        yield _sse_done()


def _sse_error(message: str, detail: str | None = None) -> str:
    payload = {"type": "error", "message": message}
    if detail:
        payload["detail"] = detail
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _sse_done() -> str:
    return f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
