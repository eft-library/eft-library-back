import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from redis.exceptions import RedisError
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from database import V3Database
from api.live_map.party_v3.router import publish_party_change_v3
from api.live_map.party_v3.security import authenticate_party_user_v3
from api.live_map.party_v3.schemas import PartyResponseV3, PartySnapshotV3
from .schemas import (
    ChatInvitePreferencesResponseV3, ChatInvitePreferencesUpdateV3, ChatConnectionResponseV3, ChatHistoryResponseV3, ChatUserResponseV3, ChatBlockResponseV3, ChatIdResponseV3,
    ChatRestrictionDetailV3, ChatModerationStateV3, PartyNotificationsV3, ChatUserActionsV3,
    ChatDeletedResponseV3, ChatRestrictionResponseV3, ChatReportResponseV3, InvitationResponseV3,
)
from .lifecycle import chat_lifespan_v3
from .schemas import ChannelV3, ChatReportCreateV3, ChatRestrictionCreateV3, InvitationCreateV3, StatusV3
from .security import GUEST_COOKIE_NAME_V3, optional_chat_user_v3
from .service import ChatServiceV3
from .store import get_chat_store_v3

logger_v3 = logging.getLogger('api.live_map.chat_v3')


async def publish_committed_v3(session):
    available = True
    events = session.info.pop('chat_events_v3', [])
    if events:
        try:
            store = await run_in_threadpool(get_chat_store_v3)
            await run_in_threadpool(store.publish_v3, events)
        except (RedisError, HTTPException) as exc:
            logger_v3.warning('Chat notification unavailable (%s)', type(exc).__name__)
            available = False
    room_id = session.info.pop('chat_party_room_v3', None)
    if room_id:
        available = await publish_party_change_v3(room_id) and available
    return available


class ChatRouteV3(APIRoute):
    def get_route_handler(self):
        original_v3 = super().get_route_handler()

        async def handle_v3(request):
            try:
                response = await original_v3(request)
                session = getattr(request.state, 'chat_session_v3', None)
                if session is not None:
                    await run_in_threadpool(session.commit)
                    if not await publish_committed_v3(session):
                        response.headers['X-Chat-Realtime'] = 'unavailable'
                return response
            except RequestValidationError as exc:
                return JSONResponse(status_code=422, content={'status': 422, 'msg': 'INVALID_REQUEST', 'data': {
                    'errors': [{'loc': e['loc'], 'msg': e['msg'], 'type': e['type']} for e in exc.errors()]}})
            except HTTPException as exc:
                retry = (exc.headers or {}).get('Retry-After')
                data = {'retry_after': int(retry)} if retry else None
                return JSONResponse(status_code=exc.status_code, headers=exc.headers,
                                    content={'status': exc.status_code, 'msg': exc.detail, 'data': data})
            except IntegrityError:
                return JSONResponse(status_code=409, content={'status': 409, 'msg': 'CHAT_STATE_CONFLICT', 'data': None})
            except SQLAlchemyError as exc:
                logger_v3.warning('Chat database unavailable (%s)', type(exc).__name__)
                return JSONResponse(status_code=503, content={'status': 503, 'msg': 'CHAT_DATABASE_UNAVAILABLE', 'data': None})
        return handle_v3


router_v3 = APIRouter(prefix='/v3', tags=['Live Map Chat V3'], route_class=ChatRouteV3, lifespan=chat_lifespan_v3)


def get_chat_service_v3(request: Request):
    with V3Database.SessionLocal() as session:
        request.state.chat_session_v3 = session
        yield ChatServiceV3(session)


ServiceV3 = Annotated[ChatServiceV3, Depends(get_chat_service_v3, scope='request')]
EmailV3 = Annotated[str, Depends(authenticate_party_user_v3)]
OptionalEmailV3 = Annotated[str | None, Depends(optional_chat_user_v3)]


def response_v3(data, status=200, msg='OK'):
    return {'status': status, 'msg': msg, 'data': data}


class ChatGuestSessionRequestV3(BaseModel):
    model_config = ConfigDict(extra='forbid')
    guest_token: str | None = Field(default=None, max_length=128, strict=True)


@router_v3.post('/chat/guest-session')
def guest_session_v3(body: ChatGuestSessionRequestV3, request: Request, response: Response):
    response.headers['Cache-Control'] = 'no-store'
    token_v3 = get_chat_store_v3().guest_session_v3(
        request.cookies.get(GUEST_COOKIE_NAME_V3) or body.guest_token)
    response.set_cookie(GUEST_COOKIE_NAME_V3, token_v3, max_age=86400,
                        secure=True, httponly=True, samesite='lax', path='/')
    # Keep the explicit-token response for clients introduced before cookie mode.
    return response_v3({'guest_token': token_v3})


@router_v3.websocket('/chat/ws')
async def chat_websocket_v3(websocket: WebSocket):
    from .websocket import chat_socket_v3
    await chat_socket_v3(websocket)


@router_v3.get('/chat/messages', response_model=PartyResponseV3[ChatHistoryResponseV3],
               openapi_extra={'security': [{'HTTPBearer': []}, {}]})
def history_v3(email: OptionalEmailV3, service: ServiceV3, channel: ChannelV3, response: Response,
               room_id: UUID | None = None, before: str | None = Query(default=None, max_length=512),
               limit: int = Query(default=50, ge=1, le=100)):
    response.headers['Cache-Control'] = 'private, no-store'
    return response_v3(service.history_v3(
        service.identity_v3(email) if email is not None else None, channel, room_id, before, limit))


@router_v3.get('/chat/blocks', response_model=PartyResponseV3[list[ChatUserResponseV3]])
def list_blocks_v3(email: EmailV3, service: ServiceV3):
    return response_v3(service.blocks_v3(service.identity_v3(email)))


@router_v3.post('/chat/blocks/{user_id}', response_model=PartyResponseV3[ChatBlockResponseV3])
def block_v3(user_id: UUID, email: EmailV3, service: ServiceV3):
    return response_v3(service.block_v3(service.identity_v3(email), user_id))


@router_v3.delete('/chat/blocks/{user_id}', response_model=PartyResponseV3[ChatBlockResponseV3])
def unblock_v3(user_id: UUID, email: EmailV3, service: ServiceV3):
    return response_v3(service.block_v3(service.identity_v3(email), user_id, remove=True))


@router_v3.post('/chat/messages/{message_id}/report', response_model=PartyResponseV3[ChatIdResponseV3], status_code=201)
def report_v3(message_id: UUID, data: ChatReportCreateV3, email: EmailV3, service: ServiceV3):
    return response_v3(service.report_v3(service.identity_v3(email), message_id, data), 201)


@router_v3.delete('/chat/admin/messages/{message_id}', response_model=PartyResponseV3[ChatDeletedResponseV3])
def delete_message_v3(message_id: UUID, email: EmailV3, service: ServiceV3):
    return response_v3(service.delete_message_v3(service.identity_v3(email), message_id))


@router_v3.get('/chat/admin/reports', response_model=PartyResponseV3[list[ChatReportResponseV3]])
def reports_v3(email: EmailV3, service: ServiceV3, limit: int = Query(default=50, ge=1, le=100),
               offset: int = Query(default=0, ge=0, le=10000)):
    return response_v3(service.reports_v3(service.identity_v3(email), limit, offset))


@router_v3.put('/chat/admin/restrictions/{user_id}', response_model=PartyResponseV3[ChatRestrictionResponseV3])
def restrict_v3(user_id: UUID, data: ChatRestrictionCreateV3, email: EmailV3, service: ServiceV3):
    return response_v3(service.restrict_v3(service.identity_v3(email), user_id, data))


@router_v3.delete('/chat/admin/restrictions/{user_id}', response_model=PartyResponseV3[ChatRestrictionResponseV3])
def unrestrict_v3(user_id: UUID, email: EmailV3, service: ServiceV3):
    return response_v3(service.restrict_v3(service.identity_v3(email), user_id))


@router_v3.post('/party-invitations', response_model=PartyResponseV3[InvitationResponseV3], status_code=201)
def invite_v3(data: InvitationCreateV3, email: EmailV3, service: ServiceV3):
    return response_v3(service.create_invitation_v3(service.identity_v3(email), data), 201, 'PARTY_INVITATION_CREATED')


@router_v3.get('/party-invitations', response_model=PartyResponseV3[list[InvitationResponseV3]])
def invitations_v3(email: EmailV3, service: ServiceV3, status: StatusV3 = 'pending'):
    return response_v3(service.invitations_v3(service.identity_v3(email), status))


@router_v3.post('/party-invitations/{invitation_id}/accept', response_model=PartyResponseV3[PartySnapshotV3])
def accept_v3(invitation_id: UUID, email: EmailV3, service: ServiceV3):
    return response_v3(service.handle_invitation_v3(service.identity_v3(email), invitation_id, 'accept'))


@router_v3.post('/party-invitations/{invitation_id}/reject', response_model=PartyResponseV3[InvitationResponseV3])
def reject_v3(invitation_id: UUID, email: EmailV3, service: ServiceV3):
    return response_v3(service.handle_invitation_v3(service.identity_v3(email), invitation_id, 'reject'))


@router_v3.delete('/party-invitations/{invitation_id}', response_model=PartyResponseV3[InvitationResponseV3])
def revoke_v3(invitation_id: UUID, email: EmailV3, service: ServiceV3):
    return response_v3(service.handle_invitation_v3(service.identity_v3(email), invitation_id, 'revoke'))


@router_v3.get('/chat/me/moderation', response_model=PartyResponseV3[ChatModerationStateV3])
def moderation_v3(email: EmailV3, service: ServiceV3):
    return response_v3(service.moderation_state_v3(service.identity_v3(email)))


@router_v3.get('/chat/admin/restrictions', response_model=PartyResponseV3[list[ChatRestrictionDetailV3]])
def restrictions_v3(email: EmailV3, service: ServiceV3,
                    limit: int = Query(default=50, ge=1, le=100),
                    offset: int = Query(default=0, ge=0, le=10000)):
    return response_v3(service.restrictions_v3(service.identity_v3(email), limit, offset))


@router_v3.get('/party-invitations/notifications', response_model=PartyResponseV3[PartyNotificationsV3])
def invitation_notifications_v3(email: EmailV3, service: ServiceV3):
    return response_v3(service.notifications_v3(service.identity_v3(email)))


@router_v3.get('/chat/users/{user_id}/actions', response_model=PartyResponseV3[ChatUserActionsV3])
def user_actions_v3(user_id: UUID, email: EmailV3, service: ServiceV3, room_id: UUID | None = None):
    return response_v3(service.user_actions_v3(service.identity_v3(email), user_id, room_id))


@router_v3.get('/chat/online-users', response_model=PartyResponseV3[list[ChatUserResponseV3]],
               openapi_extra={'security': [{'HTTPBearer': []}, {}]})
def online_users_v3(email: OptionalEmailV3, service: ServiceV3, response: Response):
    response.headers['Cache-Control'] = 'private, no-store'
    if email is not None:
        service.identity_v3(email)
    return response_v3(service.online_users_v3())


@router_v3.get('/chat/admin/connections', response_model=PartyResponseV3[list[ChatConnectionResponseV3]])
def connection_history_v3(email: EmailV3, service: ServiceV3, response: Response,
                          online_only: bool = False,
                          limit: int = Query(default=50, ge=1, le=100),
                          offset: int = Query(default=0, ge=0, le=10000)):
    response.headers['Cache-Control'] = 'private, no-store'
    return response_v3(service.connection_history_v3(
        service.identity_v3(email), online_only, limit, offset))


@router_v3.get('/chat/me/party-invite-preferences', response_model=PartyResponseV3[ChatInvitePreferencesResponseV3])
def invite_preferences_v3(email: EmailV3, service: ServiceV3, response: Response):
    response.headers['Cache-Control'] = 'private, no-store'
    return response_v3(service.invite_preferences_v3(service.identity_v3(email)))


@router_v3.put('/chat/me/party-invite-preferences', response_model=PartyResponseV3[ChatInvitePreferencesResponseV3])
def set_invite_preferences_v3(data: ChatInvitePreferencesUpdateV3, email: EmailV3,
                              service: ServiceV3, response: Response):
    response.headers['Cache-Control'] = 'private, no-store'
    return response_v3(service.set_invite_preferences_v3(service.identity_v3(email), data.allow_party_invites))
