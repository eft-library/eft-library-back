from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from api.constants import Message
from api.kord_breach.req_models import (
    DeleteKordBreachPresetV3,
    SaveKordBreachPresetV3,
)
from api.kord_breach.service import KordBreachServiceV3
from api.response import CustomResponse
from api.user.util import UserUtil
from util.constants import HTTPCode

router = APIRouter(tags=["KORD BREACH"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@router.get("/v3/modifiers")
def get_kord_breach_modifiers_v3():
    result = KordBreachServiceV3.get_modifiers_v3()
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get(
    "/v3/presets",
    include_in_schema=False,
)
def get_kord_breach_presets_v3(token: Optional[str] = Depends(oauth2_scheme)):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)

    result = KordBreachServiceV3.get_presets_v3(user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post(
    "/v3/save-preset",
    include_in_schema=False,
)
def save_kord_breach_preset_v3(
    request_info: SaveKordBreachPresetV3,
    token: str = Depends(oauth2_scheme),
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if not user_email:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)

    result = KordBreachServiceV3.save_preset_v3(request_info, user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post(
    "/v3/delete-preset",
    include_in_schema=False,
)
def delete_kord_breach_preset_v3(
    request_info: DeleteKordBreachPresetV3,
    token: str = Depends(oauth2_scheme),
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if not user_email:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)

    result = KordBreachServiceV3.delete_preset_v3(request_info, user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/random")
def get_kord_breach_random_v3():
    result = KordBreachServiceV3.random_selection_v3()
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
