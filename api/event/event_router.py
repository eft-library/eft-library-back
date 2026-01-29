from fastapi import APIRouter, HTTPException
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.event.service import EventService

router = APIRouter(tags=["Event"])


@router.get("/board")
def get_event_quest(page: int, page_size: int):
    event_list = EventService.get_event_quest(page, page_size)
    if event_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(event_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/detail/{event_id}")
def get_event_by_id(event_id: str):
    event = EventService.get_event_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(event, HTTPCode.OK, Message.SUCCESS)
