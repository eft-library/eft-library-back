from fastapi import APIRouter, HTTPException
from api.chat.chat_req_models import ChatRequest
from api.chat.chat_res_models import ChatResponse
from api.chat.service import request_chat
import logging

log = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        return await request_chat(req)
    except Exception as e:
        log.error(f"[chat_router] error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
