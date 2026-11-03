from fastapi import APIRouter

from api.price.service import PriceService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.price.models import PriceRankReq

router = APIRouter(tags=["Item Price"])


@router.get("/v3/seasons")
def get_price_seasons():
    seasons = PriceService.get_price_seasons()
    if seasons is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(seasons, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/search")
def get_item_price(
    page: int, page_size: int, word: str, season_id: str | None = None
):
    price_list = PriceService.get_item_price(
        page, page_size, word, season_id
    )
    if price_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(price_list, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/top")
def get_item_top_price(price_rank_req: PriceRankReq):
    top_list = PriceService.get_price_top(price_rank_req)
    if top_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(top_list, HTTPCode.OK, Message.SUCCESS)
