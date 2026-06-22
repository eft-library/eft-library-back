from fastapi import APIRouter
from api.home.service import HomeServiceV3
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Home"])


@router.get("/v3/main")
def get_home_v3():
    main_info = HomeServiceV3.get_home_v3()
    if main_info is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(main_info, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/home-posts")
def get_home_posts_v3():
    home_posts = HomeServiceV3.get_home_posts_v3()
    if home_posts is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(home_posts, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/menu-with-autocomplete")
def get_home_menu_with_autocomplete_v3():
    menu_list = HomeServiceV3.get_menu_with_autocomplete_v3()
    if menu_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(menu_list, HTTPCode.OK, Message.SUCCESS)
