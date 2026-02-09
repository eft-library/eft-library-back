from fastapi import APIRouter, Depends
from api.response import CustomResponse
from fastapi.security import OAuth2PasswordBearer
from api.user.util import UserUtil
from util.constants import HTTPCode
from api.constants import Message
from api.progress.service import ProgressService
from api.progress.progress_req_models import ProgressItemList
from typing import Optional


router = APIRouter(tags=["Progress"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@router.get("/progress-item")
def get_progress_item(token: Optional[str] = Depends(oauth2_scheme)):
    user_email: Optional[str] = None
    if token:
        user_email = UserUtil.verify_google_token(access_token=token)

    result = ProgressService.get_user_progress(user_email)

    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post(
    "/update-progress-item",
    include_in_schema=False,
)
def update_progress_item(
    progress_item_list: ProgressItemList, token: str = Depends(oauth2_scheme)
):
    user_email = UserUtil.verify_google_token(access_token=token)
    if user_email:
        result = ProgressService.update_progress(progress_item_list, user_email)
        if result is None:
            return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
        return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
    else:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
