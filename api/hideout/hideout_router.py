from typing import Optional

from fastapi import APIRouter, Depends
from api.hideout.service import HideoutService, HideoutServiceV3
from api.hideout.hideout_req_models import (
    UpdateStationItemRequest,
    CompleteHideoutStation,
)
from fastapi.security import OAuth2PasswordBearer
from api.response import CustomResponse
from api.user.util import UserUtil
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Hideout"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@router.get("/get-station")
def get_station(token: Optional[str] = Depends(oauth2_scheme)):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)
    result = HideoutService.get_station(user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/detail/{normalized_name}")
def get_station_by_normalized_name_v3(normalized_name: str):
    result = HideoutServiceV3.get_station_by_normalized_name_v3(normalized_name)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post(
    "/save-station",
    include_in_schema=False,
)
def complete_station(
    station: CompleteHideoutStation, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = HideoutService.save_station(station.complete_list, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post(
    "/save-station-item",
    include_in_schema=False,
)
def save_station_item(
    req: UpdateStationItemRequest, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = HideoutService.save_station_item(req.user_item_list, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
