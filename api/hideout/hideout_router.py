from typing import Optional

from fastapi import APIRouter, Depends

from api.constants import Message
from api.hideout.hideout_req_models import (
    CompleteHideoutStationV3,
    UpdateStationItemRequestV3,
)
from api.hideout.service import HideoutServiceV3
from api.response import CustomResponse
from api.user.util import UserUtil
from fastapi.security import OAuth2PasswordBearer
from util.constants import HTTPCode

router = APIRouter(tags=["Hideout"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@router.get("/v3/all-item-requirements")
def get_all_item_requirements_v3():
    result = HideoutServiceV3.get_all_item_requirements_v3()
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/get-station")
def get_station_v3(token: Optional[str] = Depends(oauth2_scheme)):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)
    result = HideoutServiceV3.get_station_v3(user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/detail/{normalized_name}")
def get_station_by_normalized_name_v3(normalized_name: str):
    result = HideoutServiceV3.get_station_by_normalized_name_v3(normalized_name)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/save-station", include_in_schema=False)
def save_station_v3(
    station: CompleteHideoutStationV3, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = HideoutServiceV3.save_station_v3(station.complete_list, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/save-station-item", include_in_schema=False)
def save_station_item_v3(
    req: UpdateStationItemRequestV3, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = HideoutServiceV3.save_station_item_v3(req.user_item_list, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
