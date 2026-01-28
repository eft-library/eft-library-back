from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.minigame.minigame_service import MinigameService
from api.minigame.req_models import SaveScore

router = APIRouter(tags=["Minigame"])


@router.get("/rng-item")
def get_rng_item_list():
    rng_item_list = MinigameService.get_rng_item_list()
    if rng_item_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.MINIGAME_FAIL)
    return CustomResponse.response(rng_item_list, HTTPCode.OK, Message.SUCCESS)


@router.post("/rng-item/save")
def save_rng_score(request: SaveScore):
    rng_item_list = MinigameService.insert_user_minigame_score(request)
    if rng_item_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.MINIGAME_FAIL)
    return CustomResponse.response(rng_item_list, HTTPCode.OK, Message.SUCCESS)
