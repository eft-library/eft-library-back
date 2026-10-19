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

from database import V3Database
from .req_models import RaidStateRequestV3
from .desktop_contract_v3 import MAP_SLUGS_V3

logger_v3 = logging.getLogger('api.where_am_i.analytics_v3')
ENDPOINTS_V3 = {'send-raid-state', 'send-log-location', 'check-version', 'map-aliases', 'path-reports'}
FIELDS_V3 = {'body', 'query', 'path', 'email', 'map', 'started_at', 'is_active', 'transit_count',
             'session_id', 'timer_observed_at', 'raid_ends_at', 'product', 'current_version',
             'platform', 'architecture', 'channel', 'path_type', 'app_version', 'x', 'y', 'z', 'observed_at'}


class RaidStateEventV3(V3Database.Base):
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


class VersionCheckEventV3(V3Database.Base):
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


class DesktopApiFailureV3(V3Database.Base):
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


def user_key_v3(email_v3):
    return hashlib.sha256(email_v3.encode()).hexdigest()


def write_analytics_v3(endpoint_v3, payload_v3, response_v3, status_v3, fields_v3,
                       received_v3, elapsed_v3, event_id_v3, resolved_map_v3=None, map_resolved_v3=False):
    try:
        requested_map_v3 = payload_v3.get('map') if endpoint_v3 == 'send-raid-state' else None
        if (not isinstance(requested_map_v3, str) or len(requested_map_v3) > 4096
                or '\x00' in requested_map_v3):
            requested_map_v3 = None
        data_v3 = response_v3.get('data')
        success_v3 = (200 <= status_v3 < 300 and response_v3.get('msg') == 'OK'
                      and data_v3 is not None and data_v3 is not False)
        detail_v3 = response_v3.get('detail')
        code_v3 = (detail_v3 if isinstance(detail_v3, str) else
                   'REQUEST_VALIDATION_ERROR' if fields_v3 or status_v3 == 422 else
                   response_v3.get('msg', f'HTTP_{status_v3}'))
        code_v3 = str(code_v3)[:80]
        common_v3 = {'http_status':status_v3, 'result_code':code_v3,
                     'is_success':success_v3, 'elapsed_ms':elapsed_v3, 'received_at':received_v3}
        rows_v3 = []
        identity_v3 = None
        # 422 bodies are deliberately not persisted, including user-supplied values.
        if endpoint_v3 == 'send-raid-state' and status_v3 != 422:
            report_v3 = RaidStateRequestV3.model_validate(payload_v3)
            identity_v3 = user_key_v3(report_v3.email)
            state_v3 = report_v3.model_dump(mode='json', exclude={'email'})
            map_slug_v3 = resolved_map_v3 if map_resolved_v3 else report_v3.map if report_v3.map in MAP_SLUGS_V3 else None
            state_v3['map'] = map_slug_v3
            state_hash_v3 = hashlib.sha256(json.dumps(state_v3, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            rows_v3.append(RaidStateEventV3(
                user_key=identity_v3, email=report_v3.email,
                session_id=report_v3.session_id, map_slug=map_slug_v3,
                requested_map=requested_map_v3,
                started_at=report_v3.started_at, timer_observed_at=report_v3.timer_observed_at,
                raid_ends_at=report_v3.raid_ends_at, is_active=report_v3.is_active,
                transit_count=report_v3.transit_count, state_hash=state_hash_v3,
                event_id=UUID(event_id_v3) if event_id_v3 else None, **common_v3))
        if endpoint_v3 == 'check-version' and status_v3 != 422:
            result_v3 = data_v3 if isinstance(data_v3, dict) else {}
            rows_v3.append(VersionCheckEventV3(
                **{key_v3:payload_v3[key_v3] for key_v3 in
                   ('product', 'current_version', 'platform', 'architecture', 'channel')},
                **{key_v3:result_v3.get(key_v3) for key_v3 in
                   ('latest_version', 'min_supported_version', 'update_available', 'update_required')},
                **common_v3))
        if not success_v3:
            version_v3 = None
            if status_v3 != 422:
                version_v3 = payload_v3.get('current_version') if endpoint_v3 == 'check-version' else payload_v3.get('app_version')
            rows_v3.append(DesktopApiFailureV3(
                endpoint=endpoint_v3, http_status=status_v3, result_code=code_v3,
                app_version=version_v3, user_key=identity_v3, error_fields=fields_v3,
                requested_map=requested_map_v3,
                elapsed_ms=elapsed_v3, received_at=received_v3))
        if rows_v3:
            # Separate transaction, after the HTTP body has been sent. Never shares
            # or rolls back the operational API transaction/publication.
            with V3Database.SessionLocal.begin() as session_v3:
                session_v3.execute(text("set local statement_timeout = '1000ms'"))
                session_v3.execute(text("set local lock_timeout = '250ms'"))
                session_v3.add_all(rows_v3)
    except Exception as error_v3:
        # Exceptions can embed parameters; no raw paths/emails/payloads in logs.
        logger_v3.warning('Desktop analytics skipped endpoint=%s error=%s', endpoint_v3, type(error_v3).__name__)


class DesktopAnalyticsRouteV3(APIRoute):
    def get_route_handler(self):
        original_v3 = super().get_route_handler()

        async def handle_v3(request_v3):
            endpoint_v3 = request_v3.url.path.rsplit('/', 1)[-1]
            if endpoint_v3 not in ENDPOINTS_V3:
                return await original_v3(request_v3)
            started_v3 = time.perf_counter()
            received_v3 = datetime.now(timezone.utc)
            request_v3.state.desktop_analytics_v3 = {}
            fields_v3 = []
            try:
                response_v3 = await original_v3(request_v3)
            except RequestValidationError as error_v3:
                fields_v3 = sorted({'.'.join(str(part_v3) if isinstance(part_v3, int) or part_v3 in FIELDS_V3 else '<extra>'
                                             for part_v3 in item_v3['loc'])
                                    for item_v3 in error_v3.errors()})[:32]
                response_v3 = await request_validation_exception_handler(request_v3, error_v3)
            except HTTPException as error_v3:
                response_v3 = await http_exception_handler(request_v3, error_v3)
            # Collection failures must not replace a completed operational response.
            try:
                try:
                    payload_v3 = await request_v3.json() if request_v3.method == 'POST' else {}
                except (ValueError, UnicodeDecodeError):
                    payload_v3 = {}
                if not isinstance(payload_v3, dict):
                    payload_v3 = {}
                if response_v3.status_code == 422:
                    # Only the specifically requested raw map field survives validation failure.
                    payload_v3 = {'map': payload_v3.get('map')} if endpoint_v3 == 'send-raid-state' else {}
                result_v3 = json.loads(response_v3.body)
                task_v3 = BackgroundTask(write_analytics_v3, endpoint_v3, payload_v3, result_v3,
                    response_v3.status_code, fields_v3, received_v3,
                    max(0, round((time.perf_counter()-started_v3)*1000)),
                    request_v3.state.desktop_analytics_v3.get('event_id'),
                    request_v3.state.desktop_analytics_v3.get('map_slug'),
                    request_v3.state.desktop_analytics_v3.get('map_resolved', False))
                if response_v3.background is None:
                    response_v3.background = task_v3
                else:
                    response_v3.background = BackgroundTasks([response_v3.background, task_v3])
            except Exception as error_v3:
                logger_v3.warning('Desktop analytics preparation skipped (%s)', type(error_v3).__name__)
            return response_v3
        return handle_v3
