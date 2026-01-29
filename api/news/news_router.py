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


@router.get("/information/board")
def get_event_quest(page: int, page_size: int, info_type: str):
    event_list = NewsService.get_information_list(page, page_size, info_type)
    if event_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(event_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/information/{info_type}/detail/{information_id}")
def get_information_by_id(info_type: str, information_id: str):
    if info_type not in ["PATCH-NOTES", "NOTICE", "EVENT"]:
        raise HTTPException(status_code=400, detail="Invalid information type")

    information = NewsService.get_information_by_id(information_id, info_type)
    if information is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(information, HTTPCode.OK, Message.SUCCESS)
