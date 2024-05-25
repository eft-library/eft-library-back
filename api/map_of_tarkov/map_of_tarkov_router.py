from fastapi import APIRouter
from api.map_of_tarkov.service import MapOfTarkovService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Map Of Tarkov"])


@router.get("/detail/{map_id}")
def get_map_of_tarkov(map_id: str):
    map_of_tarkov = MapOfTarkovService.get_map_of_tarkov(map_id)
    if map_of_tarkov is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.MAP_OF_TARKOV_NOT_FOUND)
    return CustomResponse.response(map_of_tarkov, HTTPCode.OK, Message.SUCCESS)
