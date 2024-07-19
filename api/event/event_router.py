from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.event.service import EventService

router = APIRouter(tags=["Event"])


@router.get("/all")
def get_all_event():
    event_list = EventService.get_all_event()
    if event_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.EVENT_NOT_FOUND)
    return CustomResponse.response(event_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/detail/{event_id}")
def get_quest_by_id(event_id: str):
    event = EventService.get_event_by_id(event_id)
    if event is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.EVENT_NOT_FOUND)
    return CustomResponse.response(event, HTTPCode.OK, Message.SUCCESS)
