from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
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
    CheckFollow,
    PostDelete,
    GetUpdatePostDetail,
)


router = APIRouter(tags=["Community"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


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
def get_posts(category: str, page_num: int):
    result = CommunityService.get_posts(category, page_num)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/detail")
def get_posts_detail(request_info: GetPostDetail):
    result = CommunityService.get_detail_post(
        request_info.url, request_info.user_email, request_info.page_category
    )
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
        result = CommunityService.toggle_follow(
            request_info.following_user_email, user_email
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/check_follow")
def check_follow(
    request_info: CheckFollow,
):
    result = CommunityService.check_user_following(
        request_info.following_user_email, request_info.user_email
    )
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/update_post")
def update_post(post_info: UpdateCommunity, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.update_post(
            post_info.id,
            post_info.slug,
            post_info.category,
            post_info.title,
            post_info.contents,
            user_email,
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/get_update_post_detail")
def get_update_post_detail(
    post_info: GetUpdatePostDetail, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.get_update_post_detail(post_info.id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/delete_post_by_admin")
def delete_post_by_admin(request_info: PostDelete, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.delete_post_by_admin(request_info.post_id)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/delete_post_by_user")
def delete_post_by_user(request_info: PostDelete, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommunityService.delete_post_by_user(request_info.post_id)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMUNITY_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
