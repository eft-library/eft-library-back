from fastapi import APIRouter, HTTPException
from api.item.service import ItemService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Item"])


@router.get("/detail/{item_url}")
def get_item_detail(item_url: str):
    item = ItemService.get_item_detail(item_url)
    if item is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(item, HTTPCode.OK, Message.SUCCESS)


@router.get("/list/{item_type}")
def get_item_list(item_type: str):
    item_map = {
        "rig": ItemService.get_rig_list,
        "glasses": ItemService.get_glasses_list,
        "face-cover": ItemService.get_face_cover_list,
        "medical": ItemService.get_medical_list,
        "container": ItemService.get_container_list,
        "arm-band": ItemService.get_arm_band_list,
        "loot": ItemService.get_loot_list,
        "ammo": ItemService.get_ammo_list,
        "provisions": ItemService.get_provisions_list,
        "key": ItemService.get_key_list,
        "armor-vest": ItemService.get_armor_vest_list,
        "backpack": ItemService.get_backpack_list,
        "headset": ItemService.get_headset_list,
        "weapon": ItemService.get_weapon_list,
        "weapon-new": ItemService.get_weapon_list_new,
        "headwear": ItemService.get_headwear_list,
    }

    item_list = item_map.get(item_type)() if item_type in item_map else None
    if item_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.ITEM_LIST_NOT_FOUNT)

    return CustomResponse.response(item_list, HTTPCode.OK, Message.SUCCESS)
