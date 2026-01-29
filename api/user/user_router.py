from fastapi import APIRouter, Depends
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from util.constants import HTTPCode
from api.constants import Message
from api.user.service import UserService
from api.user.user_req_models import (
    AddUserReq,
    UpdateUserNickname,
    ReqUserReport,
    ReqUserBlock,
    ReqUserPenalty,
)
from api.user.util import UserUtil

router = APIRouter(tags=["User"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/add")
def add_user(addUserReq: AddUserReq):
    result = UserService.add_new_user(addUserReq)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/user-info")
def get_user(token: str = Depends(oauth2_scheme)):

    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        user = UserService.get_user(user_email)
        if user is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(user, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/delete")
def delete_user(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)

    if user_email:
        result = UserService.user_delete(user_email)
        if result is False:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/update-nickname")
def update_nickname(
    request_info: UpdateUserNickname, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)

    if user_email:
        result = UserService.update_nickname(request_info.nickname, user_email)
        if result is False:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/check-nickname-duplicate")
def check_nickname_duplicate(
    request_info: UpdateUserNickname, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)

    if user_email:
        result = UserService.check_nickname_duplicate(request_info.nickname)
        if result is False:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/check-last-update-nickname")
def check_last_update_nickname(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)

    if user_email:
        result = UserService.check_last_update_nickname(user_email)
        if result is False:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/report-user")
def report_post(request_info: ReqUserReport, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.report_user(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/block-user")
def block_user(request_info: ReqUserBlock, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.block_user(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/unblock-user")
def unblock_user(request_info: ReqUserBlock, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.unblock_user(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/penalty-user")
def penalty_user(request_info: ReqUserPenalty, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.penalty_user(request_info)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/my-page/default")
def get_my_page_default(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_default(user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/my-page/info")
def get_my_page_info(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_info(user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/my-page/posts")
def get_my_page_posts(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_posts(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/my-page/comments")
def get_my_page_comments(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_comments(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/my-page/bookmarks")
def get_my_page_bookmarks(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_bookmarks(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/my-page/blocks")
def get_my_page_blocks(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_blocks(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/my-page/follow")
def get_my_page_follow(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_follow(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/my-page/notification")
def get_my_page_notification(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_notification(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
