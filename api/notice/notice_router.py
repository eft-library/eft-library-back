from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.notice.service import NoticeService

router = APIRouter(tags=["Notice"])


@router.get("/board")
def get_notice(page: int, page_size: int):
    notice_list = NoticeService.get_notice(page, page_size)
    if notice_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.NOTICE_NOT_FOUND)
    return CustomResponse.response(notice_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/detail/{notice_id}")
def get_notice_by_id(notice_id: str):
    notice_list = NoticeService.get_notice_by_id(notice_id)
    if notice_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.NOTICE_NOT_FOUND)
    return CustomResponse.response(notice_list, HTTPCode.OK, Message.SUCCESS)
