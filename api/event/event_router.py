from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.event.service import EventService

router = APIRouter(tags=["Event"])


@router.get("/all")
def get_all_event_quest():
    event_list = EventService.get_all_event_quest()
    if event_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.EVENT_NOT_FOUND)
    return CustomResponse.response(event_list, HTTPCode.OK, Message.SUCCESS)
