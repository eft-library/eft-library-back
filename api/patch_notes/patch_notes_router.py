from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.patch_notes.service import PatchNotesService

router = APIRouter(tags=["PatchNotes"])


@router.get("/board")
def get_notice(page: int, page_size: int):
    notice_list = PatchNotesService.get_patch_notes(page, page_size)
    if notice_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.PATCH_NOTES_NOT_FOUND)
    return CustomResponse.response(notice_list, HTTPCode.OK, Message.SUCCESS)
