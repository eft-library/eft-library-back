from fastapi import APIRouter
from api.boss.service import BossService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Boss"])


@router.get("/all")
def get_all_boss():
    boss_list = BossService.get_all_boss()
    if boss_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.BOSS_NOT_FOUND)
    return CustomResponse.response(boss_list, HTTPCode.OK, Message.SUCCESS)
