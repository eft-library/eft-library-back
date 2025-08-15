from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from api.user.util import UserUtil
from util.constants import HTTPCode
from api.constants import Message
from api.community.service import CommunityService
from api.community.community_req_models import (
    CreateCommunity,
    GetPostDetail,
    UpdateCommunity,
    ViewCount,
    PostReaction,
    PostBookmark,
    FollowUser,
)


router = APIRouter(tags=["Community"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    result = CommunityService.upload_image(file)
    if result is None:
        raise HTTPException(status_code=500, detail=f"이미지 처리 실패")
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/create_posts")
def create_posts(post_info: CreateCommunity, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.create_posts(post_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.get("/{category}")
def get_posts(
    category: str,
    page_num: int,
    word: Optional[str] = Query("", description="검색어"),
    search_type: str = Query("all", regex="^(all|title|comment|title_content)$"),
):
    result = CommunityService.get_posts(category, page_num, word, search_type)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/detail")
def get_posts_detail(request_info: GetPostDetail):
    result = CommunityService.get_detail_post(request_info.url, request_info.user_email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/detail-meta-data")
def get_posts_detail_meta_data(request_info: GetPostDetail):
    result = CommunityService.get_detail_post_meta_data(
        request_info.url, request_info.user_email
    )
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/like_post")
def like_post(request_info: PostReaction, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.like_post(request_info.post_id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/dislike_post")
def dislike_post(request_info: PostReaction, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.dislike_post(request_info.post_id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/bookmark_post")
def bookmark_post(request_info: PostBookmark, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.bookmark_post(request_info.post_id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/follow_user")
def follow_user(request_info: FollowUser, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.follow_user(
            request_info.following_user_email, user_email
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/unfollow_user")
def unfollow_user(request_info: FollowUser, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.unfollow_user(
            request_info.following_user_email, user_email
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/check_follow")
def check_follow(request_info: FollowUser, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.check_user_following(
            request_info.following_user_email, user_email
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(
            {"is_follow": 0}, HTTPCode.OK, Message.INVALID_USER
        )
