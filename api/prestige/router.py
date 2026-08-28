from fastapi import APIRouter

from api.constants import Message
from api.prestige.service import PrestigeServiceV3
from api.response import CustomResponse
from util.constants import HTTPCode

router = APIRouter(tags=["Prestige"])


@router.get("/v3/all")
def get_all_prestige_v3():
    result = PrestigeServiceV3.get_all_prestige_v3()
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/detail/{prestige_level}")
def get_prestige_by_level_v3(prestige_level: int):
    result = PrestigeServiceV3.get_prestige_by_level_v3(prestige_level)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
