from fastapi import APIRouter, Depends
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from api.user.util import UserUtil
from util.constants import HTTPCode
from api.constants import Message
from api.comment.service import CommentService
from api.comment.comment_req_models import (
    InsertParentComment,
    InsertChildComment,
    CommentReaction,
    GetComments,
    UpdateComment,
    DeleteComment,
)


router = APIRouter(tags=["Comment"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@router.post("/insert_parent_comment")
def insert_parent_comment(
    request_info: InsertParentComment, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentService.insert_parent_comment(
            request_info.post_id, request_info.contents, user_email
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMENT_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/insert_child_comment")
def insert_child_comment(
    request_info: InsertChildComment, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentService.inset_child_comment(
            request_info.post_id,
            request_info.parent_comment_id,
            request_info.contents,
            user_email,
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMENT_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/get_comments")
def get_comments(request_info: GetComments):
    result = CommentService.get_comment(
        request_info.post_id,
        request_info.page_num,
        request_info.issue_comment_id,
        request_info.user_email,
    )
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.COMMENT_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/like_comment")
def like_comment(request_info: CommentReaction, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentService.like_comment(request_info.comment_id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMENT_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/dislike_comment")
def dislike_comment(request_info: CommentReaction, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentService.dislike_comment(request_info.comment_id, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMENT_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/update_comment")
def update_comment(request_info: UpdateComment, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentService.update_comment(
            request_info.comment_id, request_info.contents
        )
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMENT_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/delete_comment_by_admin")
def delete_comment_by_admin(
    request_info: DeleteComment, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentService.delete_comment_by_admin(request_info.comment_id)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMENT_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/delete_comment_by_user")
def delete_comment_by_user(
    request_info: DeleteComment, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = CommentService.delete_comment_by_user(request_info.comment_id)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.COMMENT_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
