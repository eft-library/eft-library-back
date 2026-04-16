from fastapi import APIRouter, HTTPException
from api.news.service import NewsServiceV3
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["News"])


@router.get("/v3/wipe")
def get_wipe_v3():
    wipe = NewsServiceV3.get_wipe_v3()
    if wipe is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(wipe, HTTPCode.OK, Message.SUCCESS)


@router.get("/health")
async def health_check():
    return CustomResponse.response({"status": "ok"}, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/information/board")
def get_event_quest_v3(page: int, page_size: int, info_type: str):
    event_list = NewsServiceV3.get_information_list_v3(page, page_size, info_type)
    if event_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(event_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/information/{info_type}/detail/{information_id}")
def get_information_by_id_v3(info_type: str, information_id: str):
    if info_type not in ["PATCH-NOTES", "NOTICE", "EVENT"]:
        raise HTTPException(status_code=400, detail="Invalid information type")

    information = NewsServiceV3.get_information_by_id_v3(information_id, info_type)
    if information is None:
        raise HTTPException(status_code=410, detail="Removed")
    return CustomResponse.response(information, HTTPCode.OK, Message.SUCCESS)
