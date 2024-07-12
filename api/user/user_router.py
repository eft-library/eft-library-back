from fastapi import APIRouter, Depends
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from util.constants import HTTPCode
from api.constants import Message
from api.user.service import UserService
from api.user.models import (
    AddUserReq,
    UserQuestReq,
    UserQuestUpdate,
    UserQuestSuccess,
    UserQuestDelete,
)
from api.user.util import UserUtil

router = APIRouter(tags=["User"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/add")
def add_user(addUserReq: AddUserReq):
    result = UserService.add_new_user(addUserReq)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/quest")
def get_user_quest(userQuestReq: UserQuestReq, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_token(
        provider=userQuestReq.provider, access_token=token
    )
    if user_email:
        result = UserService.get_user_quest(user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/quest/update")
def get_user_quest(
    userQuestUpdate: UserQuestUpdate, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_token(
        provider=userQuestUpdate.provider, access_token=token
    )
    if user_email:
        result = UserService.update_user_quest(userQuestUpdate, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/quest/success")
def success_user_quest(
    userQuestSuccess: UserQuestSuccess, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_token(
        provider=userQuestSuccess.provider, access_token=token
    )
    if user_email:
        result = UserService.success_user_quest(userQuestSuccess, user_email)
        if result is None:
            return CustomResponse.response(
                None, HTTPCode.OK, Message.SUCCESS_QUEST_FAIL
            )
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/quest/delete")
def delete_user_quest(
    userQuestDelete: UserQuestDelete, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_token(
        provider=userQuestDelete.provider, access_token=token
    )
    if user_email:
        result = UserService.delete_user_quest(userQuestDelete, user_email)
        if result is None:
            return CustomResponse.response(
                None, HTTPCode.OK, Message.SUCCESS_QUEST_FAIL
            )
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
