from fastapi import APIRouter
from api.table_column.service import TableColumnService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Table Column"])


@router.get("/all")
def get_all_column():
    column_list = TableColumnService.get_all_column()
    if column_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.COLUMN_NOT_FOUND)
    return CustomResponse.response(column_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/info/{column_key}")
def get_all_column(column_key: str):
    column_list = TableColumnService.get_column(column_key)
    if column_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.COLUMN_NOT_FOUND)
    return CustomResponse.response(column_list, HTTPCode.OK, Message.SUCCESS)
