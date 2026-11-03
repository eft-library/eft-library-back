from typing import Optional

from fastapi import APIRouter, Depends

from api.constants import Message
from api.hideout.hideout_req_models import (
    CompleteHideoutStation,
    UpdateStationItemRequest,
)
from api.hideout.service import HideoutService
from api.response import CustomResponse
from api.user.util import UserUtil
from fastapi.security import OAuth2PasswordBearer
from util.constants import HTTPCode

router = APIRouter(tags=["Hideout"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@router.get("/v3/all-item-requirements")
def get_all_item_requirements():
    result = HideoutService.get_all_item_requirements()
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/get-station")
def get_station(token: Optional[str] = Depends(oauth2_scheme)):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)
    result = HideoutService.get_station(user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/detail/{normalized_name}")
def get_station_by_normalized_name(normalized_name: str):
    result = HideoutService.get_station_by_normalized_name(normalized_name)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/save-station", include_in_schema=False)
def save_station(
    station: CompleteHideoutStation, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = HideoutService.save_station(station.complete_list, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/save-station-item", include_in_schema=False)
def save_station_item(
    req: UpdateStationItemRequest, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = HideoutService.save_station_item(req.user_item_list, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
