from fastapi import APIRouter
from api.search.service import SearchServiceV3
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Search"])


@router.get("/v3/info")
def get_all_search_v3():
    search_list = SearchServiceV3.get_all_search_v3()
    if search_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(search_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/new-sitemap")
def get_all_sitemap_v3():
    site_list = SearchServiceV3.get_all_site_list_v3()
    if site_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(site_list, HTTPCode.OK, Message.SUCCESS)
