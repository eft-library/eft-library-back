from fastapi import APIRouter
from api.boss.service import BossService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Boss"])


@router.get("/info/{boss_id}")
def get_boss_by_id(boss_id: str):
    boss = BossService.get_boss_by_id(boss_id)
    if boss is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.BOSS_NOT_FOUND)
    return CustomResponse.response(boss, HTTPCode.OK, Message.SUCCESS)
