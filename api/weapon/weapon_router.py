from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.weapon.service import WeaponService

router = APIRouter()


@router.get("/all")
def get_all_weapon():
    weapon_list = WeaponService.get_all_weapon()
    if weapon_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.WEAPON_NOT_FOUND)
    return CustomResponse.response(weapon_list, HTTPCode.OK, Message.SUCCESS)

