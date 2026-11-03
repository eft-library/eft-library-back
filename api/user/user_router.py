from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from api.constants import Message
from api.response import CustomResponse
from api.user.service import UserService
from api.user.user_req_models import (
    AddUserReq,
    ReqUserBlock,
    ReqUserPenalty,
    ReqUserReport,
    UpdateUserNickname,
)
from api.user.util import UserUtil
from util.constants import HTTPCode

router = APIRouter(tags=["User"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/v3/add", include_in_schema=False)
def add_user(addUserReq: AddUserReq):
    result = UserService.add_new_user(addUserReq)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/user-info", include_in_schema=False)
def get_user(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        user = UserService.get_user(user_email)
        if user is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(user, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/delete", include_in_schema=False)
def delete_user(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.user_delete(user_email)
        if result is False:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/update-nickname", include_in_schema=False)
def update_nickname(
    request_info: UpdateUserNickname, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.update_nickname(request_info.nickname, user_email)
        if result is False:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/check-nickname-duplicate", include_in_schema=False)
def check_nickname_duplicate(
    request_info: UpdateUserNickname, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.check_nickname_duplicate(request_info.nickname)
        if result is False:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/report-user", include_in_schema=False)
def report_user(request_info: ReqUserReport, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.report_user(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/block-user", include_in_schema=False)
def block_user(request_info: ReqUserBlock, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.block_user(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/unblock-user", include_in_schema=False)
def unblock_user(request_info: ReqUserBlock, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.unblock_user(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/penalty-user", include_in_schema=False)
def penalty_user(request_info: ReqUserPenalty, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.penalty_user(request_info)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/default", include_in_schema=False)
def get_my_page_default(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_default(user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/info", include_in_schema=False)
def get_my_page_info(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_info(user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/posts", include_in_schema=False)
def get_my_page_posts(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_posts(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/comments", include_in_schema=False)
def get_my_page_comments(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_comments(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/bookmarks", include_in_schema=False)
def get_my_page_bookmarks(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_bookmarks(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/blocks", include_in_schema=False)
def get_my_page_blocks(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_blocks(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/follow", include_in_schema=False)
def get_my_page_follow(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_follow(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/notification", include_in_schema=False)
def get_my_page_notification(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserService.get_my_page_notification(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
