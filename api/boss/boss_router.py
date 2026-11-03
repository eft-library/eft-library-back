from fastapi import APIRouter
from api.boss.service import BossService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

from util.http_exceptions import HttpError

router = APIRouter(tags=["Boss"])


@router.get("/v3/detail/{normalized_name}")
def get_boss_by_normalized_name(normalized_name: str):
    boss = BossService.get_boss_by_normalized_name(normalized_name)
    if boss is None:
        raise HttpError.RESOURCE_REMOVED.exception()
    return CustomResponse.response(boss, HTTPCode.OK, Message.SUCCESS)
