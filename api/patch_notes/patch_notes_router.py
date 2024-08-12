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


@router.get("/detail/{patch_notes_id}")
def get_patch_notes_by_id(patch_notes_id: str):
    patch_notes = PatchNotesService.get_patch_notes_by_id(patch_notes_id)
    if patch_notes is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.PATCH_NOTES_NOT_FOUND)
    return CustomResponse.response(patch_notes, HTTPCode.OK, Message.SUCCESS)
