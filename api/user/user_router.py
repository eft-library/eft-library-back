from fastapi import APIRouter, Depends
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from util.constants import HTTPCode
from api.constants import Message
from api.user.service import UserService
from api.user.user_req_models import (
    AddUserReq,
    ChangeUserNickname,
    UserQuestReq,
    UserQuestUpdate,
    UserQuestDelete,
    UserInfoReq,
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


@router.post("/get")
def get_user(useInfoReq: UserInfoReq, token: str = Depends(oauth2_scheme)):

    user_email = UserUtil.verify_token(provider=useInfoReq.provider, access_token=token)
    if user_email:
        user = UserService.get_user(user_email)
        if user is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
        return CustomResponse.response(user, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


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


@router.post("/nickname/change")
def change_user_nickname(
    changeUserNickname: ChangeUserNickname, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_token(
        provider=changeUserNickname.provider, access_token=token
    )
    if user_email:
        result = UserService.change_user_nickname(
            changeUserNickname.nickname, user_email
        )
        print(result)
        if result == 2:
            # 30일이 지나지 않은 경우
            return CustomResponse.response(
                None, HTTPCode.FORBIDDEN, Message.NICKNAME_CHANGE_NOT_AVAILABLE
            )
        elif result == 3:
            # 중복인 케이스
            return CustomResponse.response(
                None, HTTPCode.CONFLICT, Message.NICKNAME_DUPLICATE
            )
        elif result:
            # 정상
            return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
        else:
            return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
