from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.server.service import ServerService
from api.server.server_req_models import RebuildFront
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["Server"])


@router.post("/rebuild")
def rebuild_front(rebuildFront: RebuildFront):
    if os.getenv("BUILD_KEY") == rebuildFront.rebuild_key:
        result = ServerService.rebuild_front()
    return CustomResponse.response(True, HTTPCode.OK, Message.SUCCESS)


@router.post("/save_footprint")
def save_footprint():
    result = ServerService.save_footprint()
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.KAFKA_FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
