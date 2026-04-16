from fastapi import APIRouter, HTTPException
from api.map.service import MapService, MapServiceV3
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Map"])


@router.get("/v3/detail/{normalized_name}")
def get_map_by_normalized_name_v3(normalized_name: str):
    response_map = MapServiceV3.get_map_by_normalized_name_v3(normalized_name)
    if response_map is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(response_map, HTTPCode.OK, Message.SUCCESS)
