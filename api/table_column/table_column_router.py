from fastapi import APIRouter
from api.table_column.service import TableColumnService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Table Column"])


@router.get("/weapon")
def get_weapon_column():
    weapon_column = TableColumnService.get_weapon_column()
    if weapon_column is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.COLUMN_NOT_FOUND)
    return CustomResponse.response(weapon_column, HTTPCode.OK, Message.SUCCESS)
