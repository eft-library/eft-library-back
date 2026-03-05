from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from api.chat.chat_req_models import ChatRequest
from api.chat.service import request_chat_stream, get_chat_search
import logging
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

log = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.get("/search")
def get_chat_search_list():
    chat_search_list = get_chat_search()
    if chat_search_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(chat_search_list, HTTPCode.OK, Message.SUCCESS)


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    return StreamingResponse(
        request_chat_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
