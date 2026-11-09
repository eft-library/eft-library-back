import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.modding.schemas import (
    CandidatePage, ItemDetail, ModdingResponse, PresetDetail, PresetPage, WeaponPage,
)
from api.modding.service import ModdingService
from database import Database
from util.http_exceptions import HttpError

logger = logging.getLogger(__name__)
router = APIRouter(tags=['Weapon Modding'])


def get_session():
    try:
        with Database.SessionLocal() as session:
            # A collector commit between queries must not mix old and new relationships.
            session.connection(execution_options={'isolation_level':'REPEATABLE READ'})
            session.execute(text('SET TRANSACTION READ ONLY'))
            session.execute(text("SET LOCAL statement_timeout='10s'"))
            yield session
    except SQLAlchemyError:
        logger.exception('Modding lookup failed')
        raise HttpError.MODDING_LOOKUP_UNAVAILABLE.exception() from None


SessionDependency = Annotated[Session, Depends(get_session)]
ItemId = Annotated[str, Path(min_length=1, max_length=200)]
PageNumber = Annotated[int, Query(ge=1, le=1_000_000)]
PageSize = Annotated[int, Query(ge=1, le=100)]
SearchWord = Annotated[str, Query(max_length=200)]


def success(data):
    return {'status':200,'msg':'OK','data':data}


@router.get('/v3/weapons', response_model=ModdingResponse[WeaponPage])
def get_modding_weapons(session: SessionDependency, word: SearchWord = '',
                        page: PageNumber = 1, page_size: PageSize = 50):
    return success(ModdingService.weapons(session,word,page,page_size))


@router.get('/v3/items/{item_id}', response_model=ModdingResponse[ItemDetail])
def get_modding_item(item_id: ItemId, session: SessionDependency):
    return success(ModdingService.item_detail(session,item_id))


@router.get('/v3/items/{item_id}/slots/{slot_id}/candidates',
            response_model=ModdingResponse[CandidatePage])
def get_modding_candidates(item_id: ItemId, slot_id: Annotated[str, Path(min_length=1,max_length=200)],
                           session: SessionDependency, word: SearchWord = '',
                           page: PageNumber = 1, page_size: PageSize = 50):
    return success(ModdingService.candidates(session,item_id,slot_id,word,page,page_size))


@router.get('/v3/weapons/{weapon_id}/presets', response_model=ModdingResponse[PresetPage])
def get_modding_weapon_presets(weapon_id: ItemId, session: SessionDependency,
                               page: PageNumber = 1, page_size: PageSize = 50):
    return success(ModdingService.weapon_presets(session,weapon_id,page,page_size))


@router.get('/v3/presets/{preset_id}', response_model=ModdingResponse[PresetDetail])
def get_modding_preset(preset_id: ItemId, session: SessionDependency):
    return success(ModdingService.preset_detail(session,preset_id))
