from fastapi import APIRouter
from api.item.service import ItemServiceV3
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Item"])


@router.get("/v3/info/{normalized_name}")
def get_item_info_v3(normalized_name: str):
    item = ItemServiceV3.get_item_detail_v3(normalized_name)
    if item is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(item, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/list/{item_type}")
def get_item_list_v3(item_type: str):
    item_list = ItemServiceV3.get_item_list_v3(item_type)
    if item_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(item_list, HTTPCode.OK, Message.SUCCESS)
