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


@router.post("/get-station")
def get_station(station: GetHideoutStation):
    result = HideoutService.get_station(station.user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.HIDEOUT_NOT_FOUND)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/save-station")
def complete_station(station: CompleteHideoutStation, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = HideoutService.save_station(station.complete_list, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.STATION_SAVE_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
