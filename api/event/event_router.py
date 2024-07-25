from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.event.service import EventService

router = APIRouter(tags=["Event"])


@router.get("/board")
def get_event_quest(page: int, page_size: int):
    event_list = EventService.get_event_quest(page, page_size)
    if event_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.EVENT_NOT_FOUND)
    return CustomResponse.response(event_list, HTTPCode.OK, Message.SUCCESS)
