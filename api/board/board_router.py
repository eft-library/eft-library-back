from fastapi import APIRouter, File, UploadFile, Depends
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.board.service import BoardService
from api.board.board_req_models import AddPost, LikeOrDisPost
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


@router.get("/all")
def get_posts(page: int, page_size: int):
    posts = BoardService.get_post(page, page_size)
    if posts is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.POSTS_NOT_FOUND)
    return CustomResponse.response(posts, HTTPCode.OK, Message.SUCCESS)


@router.get("/issue")
def get_issue_posts(page: int, page_size: int):
    posts = BoardService.get_issue_board(page, page_size)
    if posts is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.POSTS_NOT_FOUND)
    return CustomResponse.response(posts, HTTPCode.OK, Message.SUCCESS)


@router.get("/all/categories")
def get_board_type():
    board_type = BoardService.get_board_type()
    if board_type is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.BOARD_TYPE_NOT_FOUND)
    return CustomResponse.response(board_type, HTTPCode.OK, Message.SUCCESS)


@router.get("/{board_type}")
def get_posts(board_type: str, page: int, page_size: int):
    posts = BoardService.get_type_post(page, page_size, board_type)
    if posts is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.POSTS_NOT_FOUND)
    return CustomResponse.response(posts, HTTPCode.OK, Message.SUCCESS)


@router.get("/{board_type}/issue")
def get_issue_type_posts(board_type: str, page: int, page_size: int):
    posts = BoardService.get_type_issue_post(page, page_size, board_type)
    if posts is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.POSTS_NOT_FOUND)
    return CustomResponse.response(posts, HTTPCode.OK, Message.SUCCESS)


@router.get("/{board_type}/detail")
def get_post_by_id(board_type: str, board_id: str):
    post = BoardService.get_post_by_id(board_id, board_type)
    if post is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.POSTS_NOT_FOUND)
    return CustomResponse.response(post, HTTPCode.OK, Message.SUCCESS)
