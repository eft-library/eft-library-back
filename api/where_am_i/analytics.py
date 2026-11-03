"""Best-effort post-response desktop analytics; never stores raw request bodies."""
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Identity, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUuid
from starlette.background import BackgroundTask, BackgroundTasks

from database import Database
from .req_models import RaidStateRequest

logger = logging.getLogger('api.where_am_i.analytics')
ENDPOINTS = {'send-raid-state', 'send-log-location', 'check-version', 'map-aliases', 'path-reports'}
FIELDS = {'body', 'query', 'path', 'email', 'map', 'started_at', 'is_active', 'transit_count',
             'session_id', 'timer_observed_at', 'raid_ends_at', 'product', 'current_version',
             'platform', 'architecture', 'channel', 'path_type', 'app_version', 'x', 'y', 'z', 'observed_at'}


class RaidStateEvent(Database.Base):
    __tablename__ = 'where_am_i_raid_state_events'
    id = Column(BigInteger, Identity(), primary_key=True)
    user_key = Column(String(64), nullable=False)
    email = Column(Text)
    session_id = Column(String(64))
    map_slug = Column(Text)
    requested_map = Column(Text)
    started_at = Column(DateTime(timezone=True))
    timer_observed_at = Column(DateTime(timezone=True))
    raid_ends_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, nullable=False)
    transit_count = Column(Integer, nullable=False)
    state_hash = Column(String(64), nullable=False)
    event_id = Column(PgUuid(as_uuid=True))
    http_status = Column(Integer, nullable=False)
    result_code = Column(String(80), nullable=False)
    is_success = Column(Boolean, nullable=False)
    elapsed_ms = Column(Integer, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VersionCheckEvent(Database.Base):
    __tablename__ = 'where_am_i_version_checks'
    id = Column(BigInteger, Identity(), primary_key=True)
    product = Column(String(32), nullable=False)
    current_version = Column(String(64), nullable=False)
    platform = Column(String(32), nullable=False)
    architecture = Column(String(32), nullable=False)
    channel = Column(String(32), nullable=False)
    latest_version = Column(String(64))
    min_supported_version = Column(String(64))
    update_available = Column(Boolean)
    update_required = Column(Boolean)
    http_status = Column(Integer, nullable=False)
    result_code = Column(String(80), nullable=False)
    is_success = Column(Boolean, nullable=False)
    elapsed_ms = Column(Integer, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DesktopApiFailure(Database.Base):
    __tablename__ = 'where_am_i_api_failures'
    id = Column(BigInteger, Identity(), primary_key=True)
    endpoint = Column(String(80), nullable=False)
    http_status = Column(Integer, nullable=False)
    result_code = Column(String(80), nullable=False)
    app_version = Column(String(64))
    user_key = Column(String(64))
    requested_map = Column(Text)
    error_fields = Column(JSONB, nullable=False)
    elapsed_ms = Column(Integer, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


def user_key(email):
    return hashlib.sha256(email.encode()).hexdigest()


def write_analytics(endpoint, payload, api_response, status, fields,
                       received, elapsed, event_id, resolved_map=None, map_resolved=False):
    try:
        requested_map = payload.get('map') if endpoint == 'send-raid-state' else None
        if (not isinstance(requested_map, str) or len(requested_map) > 4096
                or '\x00' in requested_map):
            requested_map = None
        data = api_response.get('data')
        success = (200 <= status < 300 and api_response.get('msg') == 'OK'
                      and data is not None and data is not False)
        detail = api_response.get('detail')
        code = (detail if isinstance(detail, str) else
                   'REQUEST_VALIDATION_ERROR' if fields or status == 422 else
                   api_response.get('msg', f'HTTP_{status}'))
        code = str(code)[:80]
        common = {'http_status':status, 'result_code':code,
                     'is_success':success, 'elapsed_ms':elapsed, 'received_at':received}
        rows = []
        identity = None
        # 422 bodies are deliberately not persisted, including user-supplied values.
        if endpoint == 'send-raid-state' and status != 422:
            report = RaidStateRequest.model_validate(payload)
            identity = user_key(report.email)
            connection_state = report.model_dump(mode='json', exclude={'email'})
            map_slug = resolved_map if map_resolved else None
            connection_state['map'] = map_slug
            state_hash = hashlib.sha256(json.dumps(connection_state, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            # Empty inactive snapshots still reach clients, but add no raid analytics.
            empty_inactive = (not report.is_active and not report.map
                                 and report.started_at is None
                                 and report.timer_observed_at is None
                                 and report.raid_ends_at is None)
            if not empty_inactive:
                rows.append(RaidStateEvent(
                    user_key=identity, email=report.email,
                    session_id=report.session_id, map_slug=map_slug,
                    requested_map=requested_map,
                    started_at=report.started_at, timer_observed_at=report.timer_observed_at,
                    raid_ends_at=report.raid_ends_at, is_active=report.is_active,
                    transit_count=report.transit_count, state_hash=state_hash,
                    event_id=UUID(event_id) if event_id else None, **common))
        if endpoint == 'check-version' and status != 422:
            result = data if isinstance(data, dict) else {}
            rows.append(VersionCheckEvent(
                **{key:payload[key] for key in
                   ('product', 'current_version', 'platform', 'architecture', 'channel')},
                **{key:result.get(key) for key in
                   ('latest_version', 'min_supported_version', 'update_available', 'update_required')},
                **common))
        if not success:
            version = None
            if status != 422:
                version = payload.get('current_version') if endpoint == 'check-version' else payload.get('app_version')
            rows.append(DesktopApiFailure(
                endpoint=endpoint, http_status=status, result_code=code,
                app_version=version, user_key=identity, error_fields=fields,
                requested_map=requested_map,
                elapsed_ms=elapsed, received_at=received))
        if rows:
            # Separate transaction, after the HTTP body has been sent. Never shares
            # or rolls back the operational API transaction/publication.
            with Database.SessionLocal.begin() as session:
                session.execute(text("set local statement_timeout = '1000ms'"))
                session.execute(text("set local lock_timeout = '250ms'"))
                session.add_all(rows)
    except Exception as error:
        # Exceptions can embed parameters; no raw paths/emails/payloads in logs.
        logger.warning('Desktop analytics skipped endpoint=%s error=%s', endpoint, type(error).__name__)


class DesktopAnalyticsRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handle(request):
            endpoint = request.url.path.rsplit('/', 1)[-1]
            if endpoint not in ENDPOINTS:
                return await original(request)
            started = time.perf_counter()
            received = datetime.now(timezone.utc)
            request.state.desktop_analytics = {}
            fields = []
            try:
                api_response = await original(request)
            except RequestValidationError as error:
                fields = sorted({'.'.join(str(part) if isinstance(part, int) or part in FIELDS else '<extra>'
                                             for part in item['loc'])
                                    for item in error.errors()})[:32]
                api_response = await request_validation_exception_handler(request, error)
            except HTTPException as error:
                api_response = await http_exception_handler(request, error)
            # Collection failures must not replace a completed operational response.
            try:
                try:
                    payload = await request.json() if request.method == 'POST' else {}
                except (ValueError, UnicodeDecodeError):
                    payload = {}
                if not isinstance(payload, dict):
                    payload = {}
                if api_response.status_code == 422:
                    # Only the specifically requested raw map field survives validation failure.
                    payload = {'map': payload.get('map')} if endpoint == 'send-raid-state' else {}
                result = json.loads(api_response.body)
                task = BackgroundTask(write_analytics, endpoint, payload, result,
                    api_response.status_code, fields, received,
                    max(0, round((time.perf_counter()-started)*1000)),
                    request.state.desktop_analytics.get('event_id'),
                    request.state.desktop_analytics.get('map_slug'),
                    request.state.desktop_analytics.get('map_resolved', False))
                if api_response.background is None:
                    api_response.background = task
                else:
                    api_response.background = BackgroundTasks([api_response.background, task])
            except Exception as error:
                logger.warning('Desktop analytics preparation skipped (%s)', type(error).__name__)
            return api_response
        return handle
