from fastapi import APIRouter
from api.home.service import MenuService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Home"])


# TODO: 삭제 예정
@router.get("/home")
def get_main():
    main_info = MenuService.get_main()
    if main_info is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(main_info, HTTPCode.OK, Message.SUCCESS)


@router.get("/main")
def get_home():
    main_info = MenuService.get_home()
    if main_info is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(main_info, HTTPCode.OK, Message.SUCCESS)


@router.get("/menu-with-autocomplete")
def get_home_menu_with_autocomplete():
    menu_list = MenuService.get_menu_with_autocomplete()
    if menu_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(menu_list, HTTPCode.OK, Message.SUCCESS)
