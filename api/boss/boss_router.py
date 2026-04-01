from fastapi import APIRouter, HTTPException
from api.boss.service import BossService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Boss"])


# TODO: 삭제 예정
@router.get("/info/{url_mapping}")
def get_boss_by_id(url_mapping: str):
    boss = BossService.get_boss_by_id(url_mapping)
    if boss is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(boss, HTTPCode.OK, Message.SUCCESS)


@router.get("/detail/{normalized_name}")
def get_boss_by_normalized_name(normalized_name: str):
    boss = BossService.get_boss_by_normalized_name(normalized_name)
    if boss is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(boss, HTTPCode.OK, Message.SUCCESS)
