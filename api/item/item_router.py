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


@router.get("/headwear")
def get_all_headwear():
    head_wear = ItemService.get_all_headwear()
    if head_wear is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.HEADWEAR_NOT_FOUND)
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


@router.get("/provisions")
def get_all_provisions():
    provisions = ItemService.get_all_provisions()
    if provisions is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.PROVISION_NOT_FOUND)
    return CustomResponse.response(provisions, HTTPCode.OK, Message.SUCCESS)


@router.get("/medical")
def get_all_medical():
    medical = ItemService.get_all_medical()
    if medical is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.MEDICAL_NOT_FOUND)
    return CustomResponse.response(medical, HTTPCode.OK, Message.SUCCESS)


@router.get("/ammo")
def get_all_ammo():
    ammo = ItemService.get_all_ammo()
    if ammo is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.AMMO_NOT_FOUND)
    return CustomResponse.response(ammo, HTTPCode.OK, Message.SUCCESS)


@router.get("/loot")
def get_all_loot():
    loot = ItemService.get_all_loot()
    if loot is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.LOOT_NOT_FOUND)
    return CustomResponse.response(loot, HTTPCode.OK, Message.SUCCESS)


@router.get("/face_cover")
def get_all_face_cover():
    face_cover = ItemService.get_all_face_cover()
    if face_cover is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FACE_COVER_NOT_FOUND)
    return CustomResponse.response(face_cover, HTTPCode.OK, Message.SUCCESS)


@router.get("/arm_band")
def get_all_arm_band():
    arm_band = ItemService.get_all_arm_band()
    if arm_band is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.ARM_BAND_NOT_FOUND)
    return CustomResponse.response(arm_band, HTTPCode.OK, Message.SUCCESS)


@router.get("/glasses")
def get_all_glasses():
    glasses = ItemService.get_all_glasses()
    if glasses is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.GLASSES_NOT_FOUND)
    return CustomResponse.response(glasses, HTTPCode.OK, Message.SUCCESS)
