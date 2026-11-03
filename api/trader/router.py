import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.constants import Message
from api.response import CustomResponse
from api.trader.service import TraderService
from database import Database
from util.constants import HTTPCode

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Trader"])
GameMode = Literal["pvp", "pve", "pvp-season"]


def get_session():
    try:
        with Database.SessionLocal() as session:
            yield session
    except SQLAlchemyError:
        logger.exception("Trader lookup failed")
        raise HTTPException(500, "Trader lookup failed") from None


SessionDependency = Annotated[Session, Depends(get_session)]


def success(data):
    return CustomResponse.response(data, HTTPCode.OK, Message.SUCCESS)


@router.get("/v3/list")
def get_traders(session: SessionDependency, game_mode: GameMode = "pvp",
                season_id: str | None = Query(None, min_length=1)):
    season_id = TraderService.resolve_season(session, game_mode, season_id)
    return success(TraderService.get_traders(session, game_mode, season_id))


@router.get("/v3/offers")
def get_trader_offers(
    session: SessionDependency,
    game_mode: GameMode = "pvp",
    season_id: str | None = Query(None, min_length=1),
    trader_id: str | None = Query(None, min_length=1),
    level: int | None = Query(None, ge=1, le=4),
    word: str = Query("", max_length=200),
    offer_type: Literal["purchase", "barter"] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    season_id = TraderService.resolve_season(session, game_mode, season_id)
    return success(TraderService.get_offers(
        session, game_mode, season_id, trader_id, level, word, offer_type, page, page_size))


@router.get("/v3/offers/{offer_id}")
def get_trader_offer(
    offer_id: str, session: SessionDependency, game_mode: GameMode = "pvp",
    season_id: str | None = Query(None, min_length=1),
):
    season_id = TraderService.resolve_season(session, game_mode, season_id)
    result = TraderService.get_offers(session, game_mode, season_id, offer_id=offer_id)
    if not result["offers"]:
        raise HTTPException(404, "Offer not found")
    return success(result["offers"][0])
