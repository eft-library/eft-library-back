from fastapi import APIRouter, HTTPException
from api.news.service import NewsService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["News"])


@router.get("/wipe")
def get_wipe():
    wipe = NewsService.get_wipe()
    if wipe is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(wipe, HTTPCode.OK, Message.SUCCESS)


@router.get("/health")
async def health_check():
    return CustomResponse.response({"status": "ok"}, HTTPCode.OK, Message.SUCCESS)


@router.get("/event/board")
def get_event_quest(page: int, page_size: int):
    event_list = NewsService.get_event_quest(page, page_size)
    if event_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(event_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/event/detail/{event_id}")
def get_event_by_id(event_id: str):
    event = NewsService.get_event_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(event, HTTPCode.OK, Message.SUCCESS)


@router.get("/notice/board")
def get_notice(page: int, page_size: int):
    notice_list = NewsService.get_notice(page, page_size)
    if notice_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(notice_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/notice/detail/{notice_id}")
def get_notice_by_id(notice_id: str):
    notice = NewsService.get_notice_by_id(notice_id)
    if notice is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(notice, HTTPCode.OK, Message.SUCCESS)


@router.get("/patch-notes/board")
def get_patch_notes(page: int, page_size: int):
    patch_notes = NewsService.get_patch_notes(page, page_size)
    if patch_notes is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(patch_notes, HTTPCode.OK, Message.SUCCESS)


@router.get("/patch-notes/detail/{patch_notes_id}")
def get_patch_notes_by_id(patch_notes_id: str):
    patch_notes = NewsService.get_patch_notes_by_id(patch_notes_id)
    if patch_notes is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(patch_notes, HTTPCode.OK, Message.SUCCESS)
