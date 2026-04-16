from fastapi import APIRouter

from api.price.service import PriceServiceV3
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.price.models import PriceRankReqV3

router = APIRouter(tags=["Item Price"])


@router.get("/v3/search")
def get_item_price_v3(page: int, page_size: int, word: str):
    price_list = PriceServiceV3.get_item_price_v3(page, page_size, word)
    if price_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(price_list, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/top")
def get_item_top_price_v3(price_rank_req_v3: PriceRankReqV3):
    top_list = PriceServiceV3.get_price_top_v3(price_rank_req_v3)
    if top_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(top_list, HTTPCode.OK, Message.SUCCESS)
