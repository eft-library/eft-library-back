from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.where_am_i.req_models import CheckWpfUser, ReqWhereAmI
from api.where_am_i.service import WhereAmIServiceV3

router = APIRouter(tags=["WhereAmI"])


@router.post(
    "/check-wpf-user",
    include_in_schema=False,
)
def check_wpf_user_v3(user: CheckWpfUser):
    result = WhereAmIServiceV3.check_wpf_user_v3(user.email)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)


@router.post("/send-location")
async def send_location_v3(where_am_i: ReqWhereAmI):
    result = await WhereAmIServiceV3.send_location_v3(where_am_i)
    if result is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
