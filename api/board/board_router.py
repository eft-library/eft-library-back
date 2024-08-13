from fastapi import APIRouter, File, UploadFile, Depends
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.board.service import BoardService
from api.board.board_req_models import (
    AddPost,
    LikeOrDisPost,
    ReportBoard,
    DeletePost,
    UpdatePost,
    AddBoardViewCount,
)
from api.user.util import UserUtil
from fastapi.security import OAuth2PasswordBearer


router = APIRouter(tags=["Board"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/upload_image")
def upload_image(file: UploadFile = File(...)):
    file_location, unique_filename, image_url = BoardService.save_file(
        file, file.filename
    )
    return CustomResponse.response(image_url, HTTPCode.OK, Message.SUCCESS)


@router.post("/add")
def add_board(addPost: AddPost, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        user = BoardService.add_new_post(addPost, user_email)
        if user is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.ADD_BOARD_FAIL)
        return CustomResponse.response(user, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/view")
def add_board_view_count(
    addBoardViewCount: AddBoardViewCount, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        user = BoardService.add_board_view_count(addBoardViewCount)
        if user is None:
            return CustomResponse.response(
                None, HTTPCode.OK, Message.ADD_BOARD_VIEW_COUNT
            )
        return CustomResponse.response(user, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/update")
def update_board(updatePost: UpdatePost, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = BoardService.update_post(updatePost)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.UPDATE_BOARD_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/like")
def user_like_post(likeOrDisPost: LikeOrDisPost, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        user = BoardService.user_like_post(likeOrDisPost, user_email)
        if user is None:
            return CustomResponse.response(
                None, HTTPCode.OK, Message.POST_LIKE_CHANGE_FAIL
            )
        return CustomResponse.response(user, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/user/like")
def is_user_like_post(
    likeOrDisPost: LikeOrDisPost, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        user = BoardService.is_user_like_post(likeOrDisPost, user_email)
        if user is None:
            return CustomResponse.response(
                None, HTTPCode.OK, Message.POST_LIKE_CHANGE_FAIL
            )
        return CustomResponse.response(user, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/report")
def report_post(reportBoard: ReportBoard, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        report = BoardService.report_board(reportBoard, user_email)
        if report is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.REPORT_FAIL)
        return CustomResponse.response(report, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.post("/delete")
def delete_post(deletePost: DeletePost, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        delete_post = BoardService.delete_board(deletePost, user_email)
        if delete_post is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.BOARD_DELETE_FAIL)
        return CustomResponse.response(delete_post, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.get("/user/write")
def get_user_write_post(page: int, page_size: int, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        user = BoardService.get_user_posts(page, page_size, user_email)
        if user is None:
            return CustomResponse.response(
                None, HTTPCode.OK, Message.USER_POSTS_NOT_FOUND
            )
        return CustomResponse.response(user, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


@router.get("/posts")
def get_posts_v2(
    page: int, page_size: int, type: str, issue: bool, word: str, search_type: str
):
    posts = BoardService.get_post_v2(page, page_size, type, issue, word, search_type)
    if posts is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.POSTS_NOT_FOUND)
    return CustomResponse.response(posts, HTTPCode.OK, Message.SUCCESS)


@router.get("/all/categories")
def get_board_type():
    board_type = BoardService.get_board_type()
    if board_type is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.BOARD_TYPE_NOT_FOUND)
    return CustomResponse.response(board_type, HTTPCode.OK, Message.SUCCESS)


@router.get("/{board_type}/detail")
def get_post_by_id(board_type: str, board_id: str):
    post = BoardService.get_post_by_id(board_id, board_type)
    if post is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.POSTS_NOT_FOUND)
    return CustomResponse.response(post, HTTPCode.OK, Message.SUCCESS)
