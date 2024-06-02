from fastapi import APIRouter
from api.item.service import ItemService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Item"])


@router.get("/headset")
def get_all_headset():
    headset = ItemService.get_all_headset()
    if headset is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.HEADSET_NOT_FOUND)
    return CustomResponse.response(headset, HTTPCode.OK, Message.SUCCESS)


@router.get("/head_wear")
def get_all_head_wear():
    head_wear = ItemService.get_all_head_wear()
    if head_wear is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.HEAD_WEAR_NOT_FOUND)
    return CustomResponse.response(head_wear, HTTPCode.OK, Message.SUCCESS)