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

from database import Database
from api.live_map.party.router import publish_party_change
from api.live_map.party.security import authenticate_party_user
from api.live_map.party.schemas import PartyResponse, PartySnapshot
from .schemas import (
    ChatInvitePreferencesResponse, ChatInvitePreferencesUpdate, ChatConnectionResponse, ChatHistoryResponse, ChatUserResponse, ChatBlockResponse, ChatIdResponse,
    ChatRestrictionDetail, ChatModerationState, PartyNotifications, ChatUserActions,
    ChatDeletedResponse, ChatRestrictionResponse, ChatReportResponse, InvitationResponse,
)
from .lifecycle import chat_lifespan
from .schemas import Channel, ChatReportCreate, ChatRestrictionCreate, InvitationCreate, Status
from .security import GUEST_COOKIE_NAME, optional_chat_user
from .service import ChatService
from .store import get_chat_store

logger = logging.getLogger('api.live_map.chat')


async def publish_committed(session):
    available = True
    events = session.info.pop('chat_events_v3', [])
    if events:
        try:
            store = await run_in_threadpool(get_chat_store)
            await run_in_threadpool(store.publish, events)
        except (RedisError, HTTPException) as exc:
            logger.warning('Chat notification unavailable (%s)', type(exc).__name__)
            available = False
    room_id = session.info.pop('chat_party_room_v3', None)
    if room_id:
        available = await publish_party_change(room_id) and available
    return available


class ChatRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handle(request):
            try:
                response = await original(request)
                session = getattr(request.state, 'chat_session', None)
                if session is not None:
                    await run_in_threadpool(session.commit)
                    if not await publish_committed(session):
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
                logger.warning('Chat database unavailable (%s)', type(exc).__name__)
                return JSONResponse(status_code=503, content={'status': 503, 'msg': 'CHAT_DATABASE_UNAVAILABLE', 'data': None})
        return handle


router = APIRouter(prefix='/v3', tags=['Live Map Chat V3'], route_class=ChatRoute, lifespan=chat_lifespan)


def get_chat_service(request: Request):
    with Database.SessionLocal() as session:
        request.state.chat_session = session
        yield ChatService(session)


Service = Annotated[ChatService, Depends(get_chat_service, scope='request')]
Email = Annotated[str, Depends(authenticate_party_user)]
OptionalEmail = Annotated[str | None, Depends(optional_chat_user)]


def api_response(data, status=200, msg='OK'):
    return {'status': status, 'msg': msg, 'data': data}


class ChatGuestSessionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    guest_token: str | None = Field(default=None, max_length=128, strict=True)


@router.post('/chat/guest-session')
def guest_session(body: ChatGuestSessionRequest, request: Request, response: Response):
    response.headers['Cache-Control'] = 'no-store'
    token = get_chat_store().guest_session(
        request.cookies.get(GUEST_COOKIE_NAME) or body.guest_token)
    response.set_cookie(GUEST_COOKIE_NAME, token, max_age=86400,
                        secure=True, httponly=True, samesite='lax', path='/')
    # Keep the explicit-token response for clients introduced before cookie mode.
    return api_response({'guest_token': token})


@router.websocket('/chat/ws')
async def chat_websocket(websocket: WebSocket):
    from .websocket import chat_socket
    await chat_socket(websocket)


@router.get('/chat/messages', response_model=PartyResponse[ChatHistoryResponse],
               openapi_extra={'security': [{'HTTPBearer': []}, {}]})
def history(email: OptionalEmail, service: Service, channel: Channel, response: Response,
               room_id: UUID | None = None, before: str | None = Query(default=None, max_length=512),
               limit: int = Query(default=50, ge=1, le=100)):
    response.headers['Cache-Control'] = 'private, no-store'
    return api_response(service.history(
        service.identity(email) if email is not None else None, channel, room_id, before, limit))


@router.get('/chat/blocks', response_model=PartyResponse[list[ChatUserResponse]])
def list_blocks(email: Email, service: Service):
    return api_response(service.blocks(service.identity(email)))


@router.post('/chat/blocks/{user_id}', response_model=PartyResponse[ChatBlockResponse])
def block(user_id: UUID, email: Email, service: Service):
    return api_response(service.block(service.identity(email), user_id))


@router.delete('/chat/blocks/{user_id}', response_model=PartyResponse[ChatBlockResponse])
def unblock(user_id: UUID, email: Email, service: Service):
    return api_response(service.block(service.identity(email), user_id, remove=True))


@router.post('/chat/messages/{message_id}/report', response_model=PartyResponse[ChatIdResponse], status_code=201)
def report(message_id: UUID, data: ChatReportCreate, email: Email, service: Service):
    return api_response(service.report(service.identity(email), message_id, data), 201)


@router.delete('/chat/admin/messages/{message_id}', response_model=PartyResponse[ChatDeletedResponse])
def delete_message(message_id: UUID, email: Email, service: Service):
    return api_response(service.delete_message(service.identity(email), message_id))


@router.get('/chat/admin/reports', response_model=PartyResponse[list[ChatReportResponse]])
def reports(email: Email, service: Service, limit: int = Query(default=50, ge=1, le=100),
               offset: int = Query(default=0, ge=0, le=10000)):
    return api_response(service.reports(service.identity(email), limit, offset))


@router.put('/chat/admin/restrictions/{user_id}', response_model=PartyResponse[ChatRestrictionResponse])
def restrict(user_id: UUID, data: ChatRestrictionCreate, email: Email, service: Service):
    return api_response(service.restrict(service.identity(email), user_id, data))


@router.delete('/chat/admin/restrictions/{user_id}', response_model=PartyResponse[ChatRestrictionResponse])
def unrestrict(user_id: UUID, email: Email, service: Service):
    return api_response(service.restrict(service.identity(email), user_id))


@router.post('/party-invitations', response_model=PartyResponse[InvitationResponse], status_code=201)
def invite(data: InvitationCreate, email: Email, service: Service):
    return api_response(service.create_invitation(service.identity(email), data), 201, 'PARTY_INVITATION_CREATED')


@router.get('/party-invitations', response_model=PartyResponse[list[InvitationResponse]])
def invitations(email: Email, service: Service, status: Status = 'pending'):
    return api_response(service.invitations(service.identity(email), status))


@router.post('/party-invitations/{invitation_id}/accept', response_model=PartyResponse[PartySnapshot])
def accept(invitation_id: UUID, email: Email, service: Service):
    return api_response(service.handle_invitation(service.identity(email), invitation_id, 'accept'))


@router.post('/party-invitations/{invitation_id}/reject', response_model=PartyResponse[InvitationResponse])
def reject(invitation_id: UUID, email: Email, service: Service):
    return api_response(service.handle_invitation(service.identity(email), invitation_id, 'reject'))


@router.delete('/party-invitations/{invitation_id}', response_model=PartyResponse[InvitationResponse])
def revoke(invitation_id: UUID, email: Email, service: Service):
    return api_response(service.handle_invitation(service.identity(email), invitation_id, 'revoke'))


@router.get('/chat/me/moderation', response_model=PartyResponse[ChatModerationState])
def moderation(email: Email, service: Service):
    return api_response(service.moderation_state(service.identity(email)))


@router.get('/chat/admin/restrictions', response_model=PartyResponse[list[ChatRestrictionDetail]])
def restrictions(email: Email, service: Service,
                    limit: int = Query(default=50, ge=1, le=100),
                    offset: int = Query(default=0, ge=0, le=10000)):
    return api_response(service.restrictions(service.identity(email), limit, offset))


@router.get('/party-invitations/notifications', response_model=PartyResponse[PartyNotifications])
def invitation_notifications(email: Email, service: Service):
    return api_response(service.notifications(service.identity(email)))


@router.get('/chat/users/{user_id}/actions', response_model=PartyResponse[ChatUserActions])
def user_actions(user_id: UUID, email: Email, service: Service, room_id: UUID | None = None):
    return api_response(service.user_actions(service.identity(email), user_id, room_id))


@router.get('/chat/online-users', response_model=PartyResponse[list[ChatUserResponse]],
               openapi_extra={'security': [{'HTTPBearer': []}, {}]})
def online_users(email: OptionalEmail, service: Service, response: Response):
    response.headers['Cache-Control'] = 'private, no-store'
    if email is not None:
        service.identity(email)
    return api_response(service.online_users())


@router.get('/chat/admin/connections', response_model=PartyResponse[list[ChatConnectionResponse]])
def connection_history(email: Email, service: Service, response: Response,
                          online_only: bool = False,
                          limit: int = Query(default=50, ge=1, le=100),
                          offset: int = Query(default=0, ge=0, le=10000)):
    response.headers['Cache-Control'] = 'private, no-store'
    return api_response(service.connection_history(
        service.identity(email), online_only, limit, offset))


@router.get('/chat/me/party-invite-preferences', response_model=PartyResponse[ChatInvitePreferencesResponse])
def invite_preferences(email: Email, service: Service, response: Response):
    response.headers['Cache-Control'] = 'private, no-store'
    return api_response(service.invite_preferences(service.identity(email)))


@router.put('/chat/me/party-invite-preferences', response_model=PartyResponse[ChatInvitePreferencesResponse])
def set_invite_preferences(data: ChatInvitePreferencesUpdate, email: Email,
                              service: Service, response: Response):
    response.headers['Cache-Control'] = 'private, no-store'
    return api_response(service.set_invite_preferences(service.identity(email), data.allow_party_invites))
