from fastapi import APIRouter
from api.home.service import MenuService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Home"])


@router.get("/home")
def get_main():
    main_info = MenuService.get_main()
    if main_info is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.MAIN_INFO_NOT_FOUND)
    return CustomResponse.response(main_info, HTTPCode.OK, Message.SUCCESS)

