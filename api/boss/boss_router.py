from fastapi import APIRouter, HTTPException
from api.boss.service import BossServiceV3
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Boss"])


@router.get("/v3/detail/{normalized_name}")
def get_boss_by_normalized_name_v3(normalized_name: str):
    boss = BossServiceV3.get_boss_by_normalized_name_v3(normalized_name)
    if boss is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(boss, HTTPCode.OK, Message.SUCCESS)
