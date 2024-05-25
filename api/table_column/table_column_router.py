from fastapi import APIRouter
from api.table_column.service import TableColumnService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Table Column"])


@router.get("/column/{column_id}")
def get_column(column_id: str):
    column = TableColumnService.get_column(column_id)
    if column is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.COLUMN_NOT_FOUND)
    return CustomResponse.response(column, HTTPCode.OK, Message.SUCCESS)
