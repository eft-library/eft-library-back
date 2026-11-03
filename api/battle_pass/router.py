from fastapi import APIRouter

from api.battle_pass.service import BattlePassService
from api.constants import Message
from api.response import CustomResponse
from util.constants import HTTPCode

router = APIRouter(tags=["Battle Pass"])


@router.get("/v3/active")
def get_active_battle_pass():
    result = BattlePassService.get_active_battle_pass()
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/detail/{season_code}")
def get_battle_pass_by_code(season_code: str):
    result = BattlePassService.get_battle_pass_by_code(season_code)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
