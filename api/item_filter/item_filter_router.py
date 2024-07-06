from fastapi import APIRouter
from api.item_filter.service import ItemFilterService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["ItemFilter"])


@router.get("/all")
def get_all_item_filter():
    item_filter = ItemFilterService.get_all_item_filter()
    if item_filter is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.ITEM_FILTER_NOT_FOUND)
    return CustomResponse.response(item_filter, HTTPCode.OK, Message.SUCCESS)


@router.get("/sub_info")
def get_all_item_filter():
    item_filter = ItemFilterService.get_all_sub_item_filter_categories()
    if item_filter is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.ITEM_FILTER_NOT_FOUND)
    return CustomResponse.response(item_filter, HTTPCode.OK, Message.SUCCESS)
