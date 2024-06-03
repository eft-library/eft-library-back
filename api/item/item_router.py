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


@router.get("/armor_vest")
def get_all_head_wear():
    armor_vest = ItemService.get_all_armo_vest()
    if armor_vest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.ARMOR_VEST_NOT_FOUND)
    return CustomResponse.response(armor_vest, HTTPCode.OK, Message.SUCCESS)


@router.get("/rig")
def get_all_rig():
    rig = ItemService.get_all_rig()
    if rig is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.RIG_NOT_FOUND)
    return CustomResponse.response(rig, HTTPCode.OK, Message.SUCCESS)
