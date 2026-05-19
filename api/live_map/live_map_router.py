from fastapi import APIRouter

from api.constants import Message
from api.live_map.service import LiveMapServiceV3
from api.response import CustomResponse
from util.constants import HTTPCode

router = APIRouter(tags=["Live Map"])


@router.get("/v3/detail/{normalized_name}")
def get_live_map_v3(normalized_name: str):
    live_map = LiveMapServiceV3.get_live_map_v3(normalized_name)
    if live_map is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(live_map, HTTPCode.OK, Message.SUCCESS)
