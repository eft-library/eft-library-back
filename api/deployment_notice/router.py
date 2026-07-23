from fastapi import APIRouter

from api.constants import Message
from api.deployment_notice.service import DeploymentNoticeServiceV3
from api.response import CustomResponse
from util.constants import HTTPCode

router = APIRouter(tags=["Deployment Notice"])


@router.get("/v3/status")
def get_deployment_notice_v3():
    result = DeploymentNoticeServiceV3.get_deployment_notice_v3()
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
