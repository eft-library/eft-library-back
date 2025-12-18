from typing import Optional

from fastapi import APIRouter, Depends
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from util.constants import HTTPCode
from api.constants import Message
from api.planner.planner_req_models import (
    UserQuestList,
    GetUserQuest,
)
from api.user.util import UserUtil
from api.planner.service import PlannerService

router = APIRouter(tags=["Planner"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/quest")
def get_user_quest(getUserQuest: GetUserQuest):
    result = PlannerService.get_user_quest(getUserQuest.user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/quest")
def get_user_quest(token: Optional[str] = Depends(oauth2_scheme)):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)
    result = PlannerService.get_user_quest(user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/quest/update")
def update_user_quest(
    userQuestList: UserQuestList, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = PlannerService.update_user_quest(userQuestList, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/quest/delete")
def delete_user_quest(
    userQuestList: UserQuestList, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = PlannerService.delete_user_quest(userQuestList, user_email)
        if result is None:
            return CustomResponse.response(
                None, HTTPCode.OK, Message.SUCCESS_QUEST_FAIL
            )
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
