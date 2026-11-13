from typing import Optional

from fastapi import APIRouter, Depends, Query
from util.auth import BearerToken

from api.constants import Message
from api.kord_breach.req_models import (
    DeleteKordBreachPreset,
    SaveKordBreachPreset,
)
from api.kord_breach.service import KordBreachService
from api.kord_breach.rewards import RewardsResult, get_rewards
from api.modding.router import SessionDependency, success
from api.modding.schemas import ModdingResponse
from api.modding.calculation_schemas import CalculationError

from api.response import CustomResponse
from api.user.util import UserUtil
from util.constants import HTTPCode

router = APIRouter(tags=["KORD BREACH"])

oauth2_scheme = BearerToken(tokenUrl="token", auto_error=False)


@router.get("/v3/modifiers")
def get_kord_breach_modifiers():
    result = KordBreachService.get_modifiers()
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get(
    "/v3/presets",
    include_in_schema=False,
)
def get_kord_breach_presets(token: Optional[str] = Depends(oauth2_scheme)):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)

    result = KordBreachService.get_presets(user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post(
    "/v3/save-preset",
    include_in_schema=False,
)
def save_kord_breach_preset(
    request_info: SaveKordBreachPreset,
    token: str = Depends(oauth2_scheme),
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if not user_email:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)

    result = KordBreachService.save_preset(request_info, user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post(
    "/v3/delete-preset",
    include_in_schema=False,
)
def delete_kord_breach_preset(
    request_info: DeleteKordBreachPreset,
    token: str = Depends(oauth2_scheme),
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if not user_email:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)

    result = KordBreachService.delete_preset(request_info, user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/random")
def get_kord_breach_random():
    result = KordBreachService.random_selection()
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get('/v3/rewards', response_model=ModdingResponse[RewardsResult], responses={
    503: {'model': CalculationError, 'description': 'KORD_REWARDS_UNAVAILABLE / MODDING_LOOKUP_UNAVAILABLE'},
})
def get_kord_breach_rewards(session: SessionDependency, season_id: str = Query('kord-breach', min_length=1, max_length=200)):
    return success(get_rewards(session, season_id))
