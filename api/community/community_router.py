from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer

from api.community.community_req_models import (
    CheckFollow,
    CreateCommunity,
    FollowUser,
    GetPostDetail,
    GetUpdatePostDetail,
    PostBookmark,
    PostDelete,
    PostReaction,
    ReqPostReport,
    UpdateCommunity,
)
from api.community.service import CommunityServiceV3
from api.constants import Message
from api.response import CustomResponse
from api.user.util import UserUtil
from util.constants import HTTPCode

router = APIRouter(tags=["Community"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@router.post("/v3/upload-image", include_in_schema=False)
async def upload_image_v3(file: UploadFile = File(...)):
    result = CommunityServiceV3.upload_image_v3(file)
    if result is None:
        raise HTTPException(status_code=500, detail="이미지 처리 실패")
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/create-posts", include_in_schema=False)
def create_posts_v3(post_info: CreateCommunity, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityServiceV3.create_posts_v3(post_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.get("/v3/get/{category}")
def get_posts_v3(
    category: str,
    page_num: int,
    token: Optional[str] = Depends(oauth2_scheme),
):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)
    result = CommunityServiceV3.get_posts_v3(category, page_num, user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/search")
def get_search_posts_v3(
    page_num: int,
    word: str,
    search_type: str,
    token: Optional[str] = Depends(oauth2_scheme),
):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)
    result = CommunityServiceV3.get_search_v3(search_type, word, page_num, user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/detail")
def get_posts_detail_v3(request_info: GetPostDetail):
    result = CommunityServiceV3.get_detail_post_v3(
        request_info.url, request_info.user_email, request_info.page_category
    )
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/side-post")
def get_side_post_v3(token: Optional[str] = Depends(oauth2_scheme)):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)
    result = CommunityServiceV3.get_side_info_v3(user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/detail-meta-data")
def get_posts_detail_meta_data_v3(request_info: GetPostDetail):
    result = CommunityServiceV3.get_detail_post_meta_data_v3(
        request_info.url, request_info.user_email
    )
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/like-post", include_in_schema=False)
def like_post_v3(request_info: PostReaction, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityServiceV3.like_post_v3(request_info.post_id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/dislike-post", include_in_schema=False)
def dislike_post_v3(request_info: PostReaction, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityServiceV3.dislike_post_v3(request_info.post_id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/bookmark-post", include_in_schema=False)
def bookmark_post_v3(request_info: PostBookmark, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityServiceV3.bookmark_post_v3(request_info.post_id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/follow-user", include_in_schema=False)
def follow_user_v3(request_info: FollowUser, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityServiceV3.toggle_follow_v3(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/check-follow", include_in_schema=False)
def check_follow_v3(request_info: CheckFollow):
    result = CommunityServiceV3.check_user_following_v3(
        request_info.following_user_email, request_info.user_email
    )
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/update-post", include_in_schema=False)
def update_post_v3(post_info: UpdateCommunity, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityServiceV3.update_post_v3(
            post_info.id,
            post_info.slug,
            post_info.category,
            post_info.title,
            post_info.contents,
            user_email,
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/get-update-post-detail", include_in_schema=False)
def get_update_post_detail_v3(
    post_info: GetUpdatePostDetail, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityServiceV3.get_update_post_detail_v3(
            post_info.post_id, user_email
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/delete-post-by-admin", include_in_schema=False)
def delete_post_by_admin_v3(
    request_info: PostDelete, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityServiceV3.delete_post_by_admin_v3(request_info.post_id)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/delete-post-by-user", include_in_schema=False)
def delete_post_by_user_v3(
    request_info: PostDelete, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityServiceV3.delete_post_by_user_v3(request_info.post_id)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/report-post", include_in_schema=False)
def report_post_v3(request_info: ReqPostReport, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityServiceV3.report_post_v3(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/increase-view-count")
def increase_view_count_v3(request_info: PostReaction):
    result = CommunityServiceV3.increase_view_count_v3(request_info.post_id)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
