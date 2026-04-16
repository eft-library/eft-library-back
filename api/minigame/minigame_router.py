from fastapi import APIRouter
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message
from api.minigame.minigame_service import MinigameServiceV3
from api.minigame.req_models import SaveScore, MyRank

router = APIRouter(tags=["Minigame"])


@router.get("/v3/rng-item")
def get_rng_item_list_v3():
    rng_item_list = MinigameServiceV3.get_rng_item_list_v3()
    if rng_item_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(rng_item_list, HTTPCode.OK, Message.SUCCESS)


@router.post(
    "/v3/rng-item/save",
    include_in_schema=False,
)
def save_rng_score_v3(request: SaveScore):
    rng_item_list = MinigameServiceV3.insert_user_minigame_score_v3(request)
    if rng_item_list is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(rng_item_list, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/rng-item/all-rank")
def get_rng_item_rank_v3():
    all_rng_item_rank = MinigameServiceV3.get_all_rng_item_rank_v3()
    if all_rng_item_rank is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(all_rng_item_rank, HTTPCode.OK, Message.SUCCESS)


@router.post("/v3/rng-item/my-rank")
def get_rng_item_my_rank_v3(request: MyRank):
    rng_item_my_rank = MinigameServiceV3.get_rng_item_my_rank_v3(request.score)
    if rng_item_my_rank is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(rng_item_my_rank, HTTPCode.OK, Message.SUCCESS)
