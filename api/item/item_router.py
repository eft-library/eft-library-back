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
    armor_vest = ItemService.get_all_armor_vest()
    if armor_vest is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.ARMOR_VEST_NOT_FOUND)
    return CustomResponse.response(armor_vest, HTTPCode.OK, Message.SUCCESS)


@router.get("/backpack")
def get_all_backpack():
    backpack = ItemService.get_all_backpack()
    if backpack is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.BACKPACK_NOT_FOUND)
    return CustomResponse.response(backpack, HTTPCode.OK, Message.SUCCESS)


@router.get("/rig")
def get_all_rig():
    rig = ItemService.get_all_rig()
    if rig is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.RIG_NOT_FOUND)
    return CustomResponse.response(rig, HTTPCode.OK, Message.SUCCESS)


@router.get("/container")
def get_all_container():
    container = ItemService.get_all_container()
    if container is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.CONTAINER_NOT_FOUND)
    return CustomResponse.response(container, HTTPCode.OK, Message.SUCCESS)


@router.get("/key")
def get_all_key():
    key = ItemService.get_all_key()
    if key is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.KEY_NOT_FOUND)
    return CustomResponse.response(key, HTTPCode.OK, Message.SUCCESS)


@router.get("/food_drink")
def get_all_food_drink():
    food_drink = ItemService.get_all_food_drink()
    if food_drink is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FOOD_DRINK_NOT_FOUND)
    return CustomResponse.response(food_drink, HTTPCode.OK, Message.SUCCESS)


@router.get("/medical")
def get_all_medical():
    medical = ItemService.get_all_medical()
    if medical is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.MEDICAL)
    return CustomResponse.response(medical, HTTPCode.OK, Message.SUCCESS)


@router.get("/ammo")
def get_all_ammo():
    ammo = ItemService.get_all_ammo()
    if ammo is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.AMMO)
    return CustomResponse.response(ammo, HTTPCode.OK, Message.SUCCESS)
