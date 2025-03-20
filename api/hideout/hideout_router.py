from fastapi import APIRouter, Depends
from api.hideout.service import HideoutService
from api.hideout.hideout_req_models import GetHideoutStation, CompleteHideoutStation, BrokenHideoutStation
from fastapi.security import OAuth2PasswordBearer
from api.response import CustomResponse
from api.user.util import UserUtil
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Hideout"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.get("/all")
def get_all_hideout():
    hideout = HideoutService.get_all_hideout()
    if hideout is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.HIDEOUT_NOT_FOUND)
    return CustomResponse.response(hideout, HTTPCode.OK, Message.SUCCESS)


@router.post("/get_station")
def get_station(station: GetHideoutStation):
    # result = HideoutService.get_station(station.user_email)
    result = None
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.HIDEOUT_NOT_FOUND)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/complete_station")
def complete_station(station: CompleteHideoutStation, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = HideoutService.complete_station(station.complete_id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.STATION_SAVE_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/broken_station")
def broken_station(station: BrokenHideoutStation, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = HideoutService.broken_station(station.broken_id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.STATION_SAVE_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
