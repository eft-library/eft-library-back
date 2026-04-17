from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from api.comment.comment_req_models import (
    CommentReaction,
    DeleteComment,
    GetComments,
    InsertChildComment,
    InsertParentComment,
    ReqCommentReport,
    UpdateComment,
)
from api.comment.service import CommentServiceV3
from api.constants import Message
from api.response import CustomResponse
from api.user.util import UserUtil
from util.constants import HTTPCode

router = APIRouter(tags=["Comment"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@router.post("/v3/insert-parent-comment", include_in_schema=False)
def insert_parent_comment_v3(
    request_info: InsertParentComment, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentServiceV3.insert_parent_comment_v3(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/insert-child-comment", include_in_schema=False)
def insert_child_comment_v3(
    request_info: InsertChildComment, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentServiceV3.insert_child_comment_v3(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/get-comments")
def get_comments_v3(request_info: GetComments):
    result = CommentServiceV3.get_comment_v3(
        request_info.post_id,
        request_info.page_num,
        request_info.issue_comment_id,
        request_info.user_email,
    )
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/like-comment", include_in_schema=False)
def like_comment_v3(request_info: CommentReaction, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentServiceV3.like_comment_v3(request_info.comment_id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/dislike-comment", include_in_schema=False)
def dislike_comment_v3(
    request_info: CommentReaction, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentServiceV3.dislike_comment_v3(
            request_info.comment_id, user_email
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/update-comment", include_in_schema=False)
def update_comment_v3(request_info: UpdateComment, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentServiceV3.update_comment_v3(
            request_info.comment_id, request_info.contents
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/delete-comment-by-admin", include_in_schema=False)
def delete_comment_by_admin_v3(
    request_info: DeleteComment, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentServiceV3.delete_comment_by_admin_v3(request_info.comment_id)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/delete-comment-by-user", include_in_schema=False)
def delete_comment_by_user_v3(
    request_info: DeleteComment, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentServiceV3.delete_comment_by_user_v3(request_info.comment_id)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)


@router.post("/v3/report-comment", include_in_schema=False)
def report_comment_v3(
    request_info: ReqCommentReport, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentServiceV3.report_comment_v3(request_info, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
