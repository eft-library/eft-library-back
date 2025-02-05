from fastapi import APIRouter

from api.price.service import PriceService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Item Price"])


@router.get("/search")
def get_item_price(page: int, page_size: int, word: str):
    price_list = PriceService.get_item_price(page, page_size, word)
    if price_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.PRICE_NOT_FOUND)
    return CustomResponse.response(price_list, HTTPCode.OK, Message.SUCCESS)
