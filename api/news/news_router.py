from fastapi import APIRouter
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
