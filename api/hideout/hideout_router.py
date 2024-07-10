from fastapi import APIRouter
from api.hideout.service import HideoutService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Hideout"])


@router.get("/all")
def get_all_hideout():
    hideout = HideoutService.get_all_hideout()
    if hideout is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.HIDEOUT_NOT_FOUND)
    return CustomResponse.response(hideout, HTTPCode.OK, Message.SUCCESS)
