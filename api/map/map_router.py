from fastapi import APIRouter, HTTPException
from api.map.service import MapService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Map"])


# TODO: 삭제 예정
@router.get("/info/{map_id}")
def get_map(map_id: str):
    response_map = MapService.get_map(map_id)
    if response_map is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(response_map, HTTPCode.OK, Message.SUCCESS)


# TODO: 삭제 예정
@router.get("/sub/{map_id}")
def get_sub_map(map_id: str):
    maps = MapService.get_sub_map(map_id)
    if maps is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(maps, HTTPCode.OK, Message.SUCCESS)


@router.get("/detail/{normalized_name}")
def get_map_by_normalized_name(normalized_name: str):
    response_map = MapService.get_map_by_normalized_name(normalized_name)
    if response_map is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(response_map, HTTPCode.OK, Message.SUCCESS)
