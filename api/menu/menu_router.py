from fastapi import APIRouter
from api.menu.service import MenuService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Menu"])


@router.get("/navi")
def get_menu():
    menu_list = MenuService.get_all_menu()
    if menu_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.MENU_NOT_FOUND)
    return CustomResponse.response(menu_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/info")
def get_main_info():
    main_info_list = MenuService.get_main_info()
    if main_info_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.MAIN_INFO_NOT_FOUND)
    return CustomResponse.response(main_info_list, HTTPCode.OK, Message.SUCCESS)
