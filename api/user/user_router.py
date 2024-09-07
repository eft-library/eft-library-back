from fastapi import APIRouter, Depends
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from util.constants import HTTPCode
from api.constants import Message
from api.user.service import UserService
from api.user.user_req_models import (
    AddUserReq,
    ChangeUserNickname,
    ChangeUserIcon,
    UserQuestList,
    BanUser,
    UserPostCommentDetail,
)
from api.user.util import UserUtil
from api.user.user_quest_service import UserQuestService

router = APIRouter(tags=["User"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/add")
def add_user(addUserReq: AddUserReq):
    result = UserService.add_new_user(addUserReq)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/post_detail")
def get_user_post_detail(
    userPostCommentDetail: UserPostCommentDetail, page: int, page_size: int
):
    result = UserService.get_user_post_detail(
        userPostCommentDetail.user_email, page, page_size
    )
    if result is None:
        return CustomResponse.response(
            None, HTTPCode.OK, Message.GET_USER_POST_DETAIL_FAIL
        )
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/comment_detail")
def get_user_comment_detail(
    userPostCommentDetail: UserPostCommentDetail, page: int, page_size: int
):
    result = UserService.get_user_comment_detail(
        userPostCommentDetail.user_email, page, page_size
    )
    if result is None:
        return CustomResponse.response(
            None, HTTPCode.OK, Message.GET_USER_COMMENT_DETAIL_FAIL
        )
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/get")
def get_user(token: str = Depends(oauth2_scheme)):

    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        user = UserService.get_user(user_email)
        if user is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
        return CustomResponse.response(user, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/ban")
def ban_user(banUser: BanUser, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.user_ban(banUser, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.USER_BAN_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/quest")
def get_user_quest(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserQuestService.get_user_quest(user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/quest/update")
def get_user_quest(userQuestList: UserQuestList, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserQuestService.update_user_quest(userQuestList, user_email)
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
        result = UserQuestService.delete_user_quest(userQuestList, user_email)
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
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.change_user_nickname(
            changeUserNickname.nickname, user_email
        )
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


@router.post("/icon/change")
def change_user_icon(
    changeUserIcon: ChangeUserIcon, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)

    if user_email:
        result = UserService.change_user_icon(changeUserIcon.icon, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/delete")
def delete_user(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)

    if user_email:
        result = UserService.user_delete(user_email)
        if result is False:
            return CustomResponse.response(None, HTTPCode.OK, Message.USER_DELETE_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
