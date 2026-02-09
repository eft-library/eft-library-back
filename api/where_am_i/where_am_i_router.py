from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.where_am_i.req_models import CheckWpfUser, ReqWhereAmI
from api.where_am_i.service import WhereAmIService

router = APIRouter(tags=["WhereAmI"])


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
