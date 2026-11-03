from fastapi import APIRouter, Request
from api.where_am_i.analytics import DesktopAnalyticsRoute
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.where_am_i.req_models import (
    CheckWpfUser,
    LogLocationRequest,
    RaidStateRequest,
    ReqWhereAmI,
)
from api.where_am_i.service import WhereAmIService
from api.where_am_i.path_reports import router as path_reports_router
from api.where_am_i.metadata import router as metadata_router

router = APIRouter(tags=["WhereAmI"], route_class=DesktopAnalyticsRoute)
router.include_router(path_reports_router)
router.include_router(metadata_router)


@router.post(
    "/check-wpf-user",
    include_in_schema=False,
)
def check_wpf_user(user: CheckWpfUser):
    result = WhereAmIService.check_wpf_user(user.email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/send-location")
async def send_location(where_am_i: ReqWhereAmI):
    result = await WhereAmIService.send_location(where_am_i)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/send-raid-state")
async def send_raid_state(raid_state: RaidStateRequest, request: Request):
    result = await WhereAmIService.send_raid_state(
        raid_state, analytics_context=request.state.desktop_analytics)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/send-log-location")
async def send_log_location(location: LogLocationRequest):
    result = await WhereAmIService.send_log_location(location)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
