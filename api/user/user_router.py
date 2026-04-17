from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from api.constants import Message
from api.response import CustomResponse
from api.user.service import UserServiceV3
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
def add_user_v3(addUserReq: AddUserReq):
    result = UserServiceV3.add_new_user_v3(addUserReq)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/user-info", include_in_schema=False)
def get_user_v3(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        user = UserServiceV3.get_user_v3(user_email)
        if user is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(user, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/delete", include_in_schema=False)
def delete_user_v3(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.user_delete_v3(user_email)
        if result is False:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/update-nickname", include_in_schema=False)
def update_nickname_v3(
    request_info: UpdateUserNickname, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.update_nickname_v3(request_info.nickname, user_email)
        if result is False:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/check-nickname-duplicate", include_in_schema=False)
def check_nickname_duplicate_v3(
    request_info: UpdateUserNickname, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.check_nickname_duplicate_v3(request_info.nickname)
        if result is False:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/report-user", include_in_schema=False)
def report_user_v3(request_info: ReqUserReport, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.report_user_v3(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/block-user", include_in_schema=False)
def block_user_v3(request_info: ReqUserBlock, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.block_user_v3(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/unblock-user", include_in_schema=False)
def unblock_user_v3(request_info: ReqUserBlock, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.unblock_user_v3(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/penalty-user", include_in_schema=False)
def penalty_user_v3(request_info: ReqUserPenalty, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.penalty_user_v3(request_info)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/default", include_in_schema=False)
def get_my_page_default_v3(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.get_my_page_default_v3(user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/info", include_in_schema=False)
def get_my_page_info_v3(token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.get_my_page_info_v3(user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/posts", include_in_schema=False)
def get_my_page_posts_v3(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.get_my_page_posts_v3(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/comments", include_in_schema=False)
def get_my_page_comments_v3(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.get_my_page_comments_v3(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/bookmarks", include_in_schema=False)
def get_my_page_bookmarks_v3(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.get_my_page_bookmarks_v3(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/blocks", include_in_schema=False)
def get_my_page_blocks_v3(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.get_my_page_blocks_v3(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/follow", include_in_schema=False)
def get_my_page_follow_v3(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.get_my_page_follow_v3(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/my-page/notification", include_in_schema=False)
def get_my_page_notification_v3(page_num: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = UserServiceV3.get_my_page_notification_v3(user_email, page_num)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
