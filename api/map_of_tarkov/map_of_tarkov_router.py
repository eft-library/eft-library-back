from fastapi import APIRouter
from api.map_of_tarkov.service import MapOfTarkovService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Map Of Tarkov"])


@router.get("/detail/{map_id}")
def get_all_boss(map_id: str):
    boss_list = MapOfTarkovService.get_map_of_tarkov(map_id)
    if boss_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.BOSS_NOT_FOUND)
    return CustomResponse.response(boss_list, HTTPCode.OK, Message.SUCCESS)
