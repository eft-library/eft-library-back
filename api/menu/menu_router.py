from fastapi import APIRouter
from api.menu.service import MenuService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Menu"])


@router.get("/menu-with-search")
def get_menu():
    menu_list = MenuService.get_menu_with_search()
    if menu_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(menu_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/menu-with-autocomplete")
def get_menu_with_autocomplete():
    menu_list = MenuService.get_menu_with_autocomplete()
    if menu_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(menu_list, HTTPCode.OK, Message.SUCCESS)
