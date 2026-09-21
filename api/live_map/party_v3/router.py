import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from database import V3Database
from .schemas import (
    PartyCreateV3, PartyDeletedV3, PartyJoinV3, PartyLeaveResponseV3,
    PartyMarkerCreateV3, PartyMarkerResponseV3, PartyMarkerUpdateV3,
    PartyMemberPatchV3, PartyMemberResponseV3, PartyOwnerTransferV3,
    PartyResponseV3, PartyRoomListV3, PartyRoomPatchV3, PartySnapshotV3,
)
from .security import authenticate_party_user_v3
from .service import PartyServiceV3


logger_v3 = logging.getLogger("api.live_map.party_v3")


class PartyRouteV3(APIRoute):
    def get_route_handler(self):
        original_v3 = super().get_route_handler()

        async def handle_v3(request: Request):
            try:
                response = await original_v3(request)
                session = getattr(request.state, "party_session_v3", None)
                if session is not None:
                    # Commit here, within error handling and before the response is sent.
                    # Yield-dependency teardown runs outside this route handler.
                    await run_in_threadpool(session.commit)
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
                logger_v3.error("Party database operation failed (%s)", type(exc).__name__)
                return JSONResponse(status_code=503, content={
                    "status": 503, "msg": "PARTY_DATABASE_UNAVAILABLE", "data": None,
                })

        return handle_v3


router_v3 = APIRouter(
    prefix="/v3/party", tags=["Live Map Party V3"], route_class=PartyRouteV3,
)


def get_party_service_v3(request: Request):
    # Session.close rolls back unsuccessful operations; PartyRouteV3 commits successes.
    with V3Database.SessionLocal() as session:
        request.state.party_session_v3 = session
        yield PartyServiceV3(session)


# Keep the session open until PartyRouteV3 has serialized and committed the response.
ServiceV3 = Annotated[PartyServiceV3, Depends(get_party_service_v3, scope="request")]
EmailV3 = Annotated[str, Depends(authenticate_party_user_v3)]


@router_v3.get("/rooms", response_model=PartyResponseV3[PartyRoomListV3])
def list_party_rooms_v3(
    service: ServiceV3,
    search: str | None = Query(default=None, min_length=1, max_length=60),
    map_id: str | None = Query(default=None, min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
):
    return PartyResponseV3(data=service.list_rooms_v3(search, map_id, limit, offset))


@router_v3.post("/rooms", status_code=201, response_model=PartyResponseV3[PartySnapshotV3])
def create_party_room_v3(data: PartyCreateV3, email: EmailV3, service: ServiceV3):
    return PartyResponseV3(status=201, data=service.create_room_v3(email, data))


@router_v3.get("/rooms/{room_id}", response_model=PartyResponseV3[PartySnapshotV3])
def get_party_room_v3(room_id: UUID, email: EmailV3, service: ServiceV3):
    return PartyResponseV3(data=service.get_room_v3(room_id, email))


@router_v3.post("/rooms/{room_id}/join", response_model=PartyResponseV3[PartySnapshotV3])
def join_party_room_v3(room_id: UUID, data: PartyJoinV3, email: EmailV3, service: ServiceV3):
    return PartyResponseV3(data=service.join_room_v3(room_id, email, data))


@router_v3.post("/rooms/{room_id}/leave", response_model=PartyResponseV3[PartyLeaveResponseV3])
def leave_party_room_v3(room_id: UUID, email: EmailV3, service: ServiceV3):
    return PartyResponseV3(data=service.leave_room_v3(room_id, email))


@router_v3.patch("/rooms/{room_id}", response_model=PartyResponseV3[PartySnapshotV3])
def patch_party_room_v3(room_id: UUID, data: PartyRoomPatchV3, email: EmailV3, service: ServiceV3):
    return PartyResponseV3(data=service.patch_room_v3(room_id, email, data))


@router_v3.delete("/rooms/{room_id}", response_model=PartyResponseV3[PartyDeletedV3])
def close_party_room_v3(room_id: UUID, email: EmailV3, service: ServiceV3):
    return PartyResponseV3(data=service.close_room_v3(room_id, email))


@router_v3.patch("/rooms/{room_id}/members/me", response_model=PartyResponseV3[PartyMemberResponseV3])
def patch_party_member_v3(room_id: UUID, data: PartyMemberPatchV3, email: EmailV3, service: ServiceV3):
    return PartyResponseV3(data=service.patch_member_v3(room_id, email, data))


@router_v3.post("/rooms/{room_id}/members/{member_id}/kick", response_model=PartyResponseV3[PartySnapshotV3])
def kick_party_member_v3(room_id: UUID, member_id: UUID, email: EmailV3, service: ServiceV3):
    return PartyResponseV3(data=service.kick_member_v3(room_id, email, member_id))


@router_v3.post("/rooms/{room_id}/owner", response_model=PartyResponseV3[PartySnapshotV3])
def transfer_party_owner_v3(room_id: UUID, data: PartyOwnerTransferV3, email: EmailV3, service: ServiceV3):
    return PartyResponseV3(data=service.transfer_owner_v3(room_id, email, data.member_id))


@router_v3.get("/rooms/{room_id}/markers", response_model=PartyResponseV3[list[PartyMarkerResponseV3]])
def list_party_markers_v3(room_id: UUID, email: EmailV3, service: ServiceV3):
    return PartyResponseV3(data=service.list_markers_v3(room_id, email))


@router_v3.post("/rooms/{room_id}/markers", status_code=201, response_model=PartyResponseV3[PartyMarkerResponseV3])
def create_party_marker_v3(room_id: UUID, data: PartyMarkerCreateV3, email: EmailV3, service: ServiceV3):
    return PartyResponseV3(status=201, data=service.create_marker_v3(room_id, email, data))


@router_v3.put("/rooms/{room_id}/markers/{marker_id}", response_model=PartyResponseV3[PartyMarkerResponseV3])
def update_party_marker_v3(
    room_id: UUID, marker_id: UUID, data: PartyMarkerUpdateV3, email: EmailV3, service: ServiceV3,
):
    return PartyResponseV3(data=service.update_marker_v3(room_id, email, marker_id, data))


@router_v3.delete("/rooms/{room_id}/markers/{marker_id}", response_model=PartyResponseV3[PartyDeletedV3])
def delete_party_marker_v3(
    room_id: UUID, marker_id: UUID, email: EmailV3, service: ServiceV3,
    version: int = Query(ge=1, le=2147483647),
):
    return PartyResponseV3(data=service.delete_marker_v3(room_id, email, marker_id, version))
