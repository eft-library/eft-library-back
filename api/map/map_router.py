from fastapi import APIRouter
from api.map.service import MapService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Map"])


@router.get("/info/{map_id}")
def get_map(map_id: str):
    response_map = MapService.get_map(map_id)
    if response_map is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.MAP_NOT_FOUND)
    return CustomResponse.response(response_map, HTTPCode.OK, Message.SUCCESS)


@router.get("/all")
def get_all_map():
    maps = MapService.get_all_map()
    if maps is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.MAP_NOT_FOUND)
    return CustomResponse.response(maps, HTTPCode.OK, Message.SUCCESS)


@router.get("/sub/{map_id}")
def get_sub_map(map_id: str):
    maps = MapService.get_sub_map(map_id)
    if maps is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.MAP_NOT_FOUND)
    return CustomResponse.response(maps, HTTPCode.OK, Message.SUCCESS)
