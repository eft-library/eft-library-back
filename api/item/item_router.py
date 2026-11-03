from fastapi import APIRouter
from api.item.service import ItemService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Item"])


@router.get("/v3/info/{normalized_name}")
def get_item_info(normalized_name: str):
    item = ItemService.get_item_detail(normalized_name)
    if item is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(item, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/list/{item_type}")
def get_item_list(item_type: str):
    item_list = ItemService.get_item_list(item_type)
    if item_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(item_list, HTTPCode.OK, Message.SUCCESS)
