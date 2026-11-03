import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from redis.exceptions import RedisError
from starlette.concurrency import run_in_threadpool

from database import Database
from .lifecycle import party_lifespan
from .realtime_store import get_party_realtime_store
from .schemas import (
    PartyCreate, PartyDeleted, PartyJoin, PartyLeaveResponse,
    PartyMarkerCreate, PartyMarkerResponse, PartyMarkerUpdate,
    PartyMemberPatch, PartyMemberResponse, PartyOwnerTransfer,
    PartyResponse, PartyRoomList, PartyRoomPatch, PartySnapshot,
)
from .security import authenticate_party_user
from .service import PartyService
from .websocket import party_socket_handler


logger = logging.getLogger("api.live_map.party")


async def publish_party_change(room_id: UUID) -> bool:
    try:
        store = await run_in_threadpool(get_party_realtime_store)
        await run_in_threadpool(store.changed, room_id)
        return True
    except (RedisError, HTTPException) as exc:
        # Persistence already succeeded. Never turn a committed write into a retryable failure.
        # Socket reconnect/heartbeat snapshots reconcile a missed notification.
        logger.warning("Party notification unavailable (%s)", type(exc).__name__)
        return False


class PartyRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handle(request: Request):
            try:
                response = await original(request)
                session = getattr(request.state, "party_session", None)
                if session is not None:
                    # Commit here, within error handling and before the response is sent.
                    # Yield-dependency teardown runs outside this route handler.
                    await run_in_threadpool(session.commit)
                    room_id = session.info.get("party_room_id_v3")
                    if room_id is not None and request.method not in ("GET", "HEAD", "OPTIONS"):
                        if not await publish_party_change(room_id):
                            response.headers["X-Party-Realtime"] = "unavailable"
                return response
            except RequestValidationError as exc:
                # FastAPI's default validation response can echo passwords in `input`.
                errors = [{"loc": e["loc"], "type": e["type"], "msg": e["msg"]} for e in exc.errors()]
                return JSONResponse(status_code=422, content={
                    "status": 422, "msg": "INVALID_REQUEST", "data": {"errors": errors},
                })
            except HTTPException as exc:
                return JSONResponse(status_code=exc.status_code, headers=exc.headers, content={
                    "status": exc.status_code, "msg": exc.detail, "data": None,
                })
            except IntegrityError:
                return JSONResponse(status_code=409, content={
                    "status": 409, "msg": "PARTY_STATE_CONFLICT", "data": None,
                })
            except SQLAlchemyError as exc:
                # SQL exception text can contain bound parameters, including hashes/emails.
                logger.error("Party database operation failed (%s)", type(exc).__name__)
                return JSONResponse(status_code=503, content={
                    "status": 503, "msg": "PARTY_DATABASE_UNAVAILABLE", "data": None,
                })

        return handle


router = APIRouter(
    prefix="/v3/party", tags=["Live Map Party V3"], route_class=PartyRoute,
    lifespan=party_lifespan,
)


@router.websocket("/rooms/{room_id}/ws")
async def party_websocket(websocket: WebSocket, room_id: UUID):
    await party_socket_handler(websocket, room_id)


def get_party_service(request: Request):
    # Session.close rolls back unsuccessful operations; PartyRouteV3 commits successes.
    with Database.SessionLocal() as session:
        request.state.party_session = session
        yield PartyService(session)


# Keep the session open until PartyRouteV3 has serialized and committed the response.
Service = Annotated[PartyService, Depends(get_party_service, scope="request")]
Email = Annotated[str, Depends(authenticate_party_user)]


@router.get("/rooms", response_model=PartyResponse[PartyRoomList])
def list_party_rooms(
    service: Service,
    search: str | None = Query(default=None, min_length=1, max_length=60),
    map_id: str | None = Query(default=None, min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
):
    return PartyResponse(data=service.list_rooms(search, map_id, limit, offset))


@router.post("/rooms", status_code=201, response_model=PartyResponse[PartySnapshot])
def create_party_room(data: PartyCreate, email: Email, service: Service):
    return PartyResponse(status=201, data=service.create_room(email, data))


@router.get("/rooms/{room_id}", response_model=PartyResponse[PartySnapshot])
def get_party_room(room_id: UUID, email: Email, service: Service):
    return PartyResponse(data=service.get_room(room_id, email))


@router.post("/rooms/{room_id}/join", response_model=PartyResponse[PartySnapshot])
def join_party_room(room_id: UUID, data: PartyJoin, email: Email, service: Service):
    return PartyResponse(data=service.join_room(room_id, email, data))


@router.post("/rooms/{room_id}/leave", response_model=PartyResponse[PartyLeaveResponse])
def leave_party_room(room_id: UUID, email: Email, service: Service):
    return PartyResponse(data=service.leave_room(room_id, email))


@router.patch("/rooms/{room_id}", response_model=PartyResponse[PartySnapshot])
def patch_party_room(room_id: UUID, data: PartyRoomPatch, email: Email, service: Service):
    return PartyResponse(data=service.patch_room(room_id, email, data))


@router.delete("/rooms/{room_id}", response_model=PartyResponse[PartyDeleted])
def close_party_room(room_id: UUID, email: Email, service: Service):
    return PartyResponse(data=service.close_room(room_id, email))


@router.patch("/rooms/{room_id}/members/me", response_model=PartyResponse[PartyMemberResponse])
def patch_party_member(room_id: UUID, data: PartyMemberPatch, email: Email, service: Service):
    return PartyResponse(data=service.patch_member(room_id, email, data))


@router.post("/rooms/{room_id}/members/{member_id}/kick", response_model=PartyResponse[PartySnapshot])
def kick_party_member(room_id: UUID, member_id: UUID, email: Email, service: Service):
    return PartyResponse(data=service.kick_member(room_id, email, member_id))


@router.delete("/rooms/{room_id}/members/{member_id}/kick", response_model=PartyResponse[PartySnapshot])
def unkick_party_member(room_id: UUID, member_id: UUID, email: Email, service: Service):
    return PartyResponse(data=service.unkick_member(room_id, email, member_id))


@router.post("/rooms/{room_id}/owner", response_model=PartyResponse[PartySnapshot])
def transfer_party_owner(room_id: UUID, data: PartyOwnerTransfer, email: Email, service: Service):
    return PartyResponse(data=service.transfer_owner(room_id, email, data.member_id))


@router.get("/rooms/{room_id}/markers", response_model=PartyResponse[list[PartyMarkerResponse]])
def list_party_markers(room_id: UUID, email: Email, service: Service):
    return PartyResponse(data=service.list_markers(room_id, email))


@router.post("/rooms/{room_id}/markers", status_code=201, response_model=PartyResponse[PartyMarkerResponse])
def create_party_marker(room_id: UUID, data: PartyMarkerCreate, email: Email, service: Service):
    return PartyResponse(status=201, data=service.create_marker(room_id, email, data))


@router.put("/rooms/{room_id}/markers/{marker_id}", response_model=PartyResponse[PartyMarkerResponse])
def update_party_marker(
    room_id: UUID, marker_id: UUID, data: PartyMarkerUpdate, email: Email, service: Service,
):
    return PartyResponse(data=service.update_marker(room_id, email, marker_id, data))


@router.delete("/rooms/{room_id}/markers/{marker_id}", response_model=PartyResponse[PartyDeleted])
def delete_party_marker(
    room_id: UUID, marker_id: UUID, email: Email, service: Service,
    version: int = Query(ge=1, le=2147483647),
):
    return PartyResponse(data=service.delete_marker(room_id, email, marker_id, version))
