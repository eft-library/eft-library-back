from fastapi import APIRouter, File, UploadFile, Depends
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.user.util import UserUtil
from fastapi.security import OAuth2PasswordBearer
from api.comment.comment_req_models import AddComment
from api.comment.service import CommentService

router = APIRouter(tags=["Comment"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/add")
def add_comment(addComment: AddComment, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        user = CommentService.add_comment(addComment, user_email)
        if user is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.ADD_COMMENT_FAIL)
        return CustomResponse.response(user, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.get("/all")
def get_comments(page: int, page_size: int, board_id: str):
    comments = CommentService.get_comment_by_id(page, page_size, board_id)
    if comments is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.COMMENTS_NOT_FOUND)
    return CustomResponse.response(comments, HTTPCode.OK, Message.SUCCESS)
