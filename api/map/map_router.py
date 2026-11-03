from fastapi import APIRouter
from api.map.service import MapService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

from util.http_exceptions import HttpError

router = APIRouter(tags=["Map"])


@router.get("/v3/detail/{normalized_name}")
def get_map_by_normalized_name(normalized_name: str):
    response_map = MapService.get_map_by_normalized_name(normalized_name)
    if response_map is None:
        raise HttpError.RESOURCE_REMOVED.exception()
    return CustomResponse.response(response_map, HTTPCode.OK, Message.SUCCESS)
