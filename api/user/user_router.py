from fastapi import APIRouter, Depends
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from util.constants import HTTPCode
from api.constants import Message
from api.user.service import UserService
from api.user.models import AddUserReq, UserQuestReq
from api.user.util import UserUtil

router = APIRouter(tags=["User"])

# JWT를 헤더에서 추출하는 의존성 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/add")
def add_user(addUserReq: AddUserReq):
    result = UserService.add_new_user(addUserReq)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/quest")
def get_user_quest(userQuestReq: UserQuestReq, token: str = Depends(oauth2_scheme)):
    user_email = UserUtil.verify_token(
        provider=userQuestReq.provider, access_token=token
    )
    if user_email:
        result = UserService.get_user_quest(user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)


# @router.post("/quest/add")
# def get_user_quest(userQuestReq: UserQuestReq, token: str = Depends(oauth2_scheme)):
#     user_email = UserUtil.verify_token(
#         provider=userQuestReq.provider, access_token=token
#     )
#     if user_email:
#         result = UserService.get_user_quest(user_email)
#         if result is None:
#             return CustomResponse.response(None, HTTPCode.OK, Message.USER_ADD_FAIL)
#         return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
#     else:
#         return CustomResponse.response(None, HTTPCode.OK, Message.INVALID_USER)
