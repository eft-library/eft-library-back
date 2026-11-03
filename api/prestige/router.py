from fastapi import APIRouter

from api.constants import Message
from api.prestige.service import PrestigeService
from api.response import CustomResponse
from util.constants import HTTPCode

router = APIRouter(tags=["Prestige"])


@router.get("/v3/all")
def get_all_prestige():
    result = PrestigeService.get_all_prestige()
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/detail/{prestige_level}")
def get_prestige_by_level(prestige_level: int):
    result = PrestigeService.get_prestige_by_level(prestige_level)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
