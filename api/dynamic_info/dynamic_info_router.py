# TODO: 전체 삭제 예정
from fastapi import APIRouter
from api.dynamic_info.service import DynamicInfoService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Dynamic Info"])


@router.get("/info/{column_key}")
def get_all_column(column_key: str):
    column_list = DynamicInfoService.get_column(column_key)
    if column_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(column_list, HTTPCode.OK, Message.SUCCESS)
