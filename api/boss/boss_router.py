from fastapi import APIRouter
from api.boss.service import BossService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Boss"])


@router.get("/info/{url_mapping}")
def get_boss_by_id(url_mapping: str):
    boss = BossService.get_boss_by_id(url_mapping)
    if boss is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.BOSS_NOT_FOUND)
    return CustomResponse.response(boss, HTTPCode.OK, Message.SUCCESS)
