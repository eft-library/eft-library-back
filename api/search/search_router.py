from fastapi import APIRouter
from api.search.service import SearchService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Search"])


@router.get("/info")
def get_all_search():
    search_list = SearchService.get_all_search()
    if search_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.SEARCH_NOT_FOUND)
    return CustomResponse.response(search_list, HTTPCode.OK, Message.SUCCESS)
