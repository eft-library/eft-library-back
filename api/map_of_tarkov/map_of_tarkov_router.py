from fastapi import APIRouter
from api.map_of_tarkov.service import MapOfTarkovService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Map Of Tarkov"])


@router.get("/v3/detail/{normalized_name}")
def get_map_of_tarkov(normalized_name: str):
    map_of_tarkov = MapOfTarkovService.get_map_of_tarkov(normalized_name)
    if map_of_tarkov is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(map_of_tarkov, HTTPCode.OK, Message.SUCCESS)
