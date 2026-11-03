"""Public desktop release and map-alias snapshots, backed by V3Database."""
import hashlib
import json
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Identity, String, Text, func, select
from sqlalchemy.exc import SQLAlchemyError

from api.constants import Message
from api.response import CustomResponse
from database import Database
from util.constants import HTTPCode
from .desktop_contract import normalize_alias, validate_download_url, version_parts
from .analytics import DesktopAnalyticsRoute

logger = logging.getLogger('api.where_am_i.metadata')
router = APIRouter(route_class=DesktopAnalyticsRoute)


class DesktopRelease(Database.Base):
    __tablename__ = 'where_am_i_releases'
    id = Column(BigInteger, Identity(), primary_key=True)
    product = Column(String(32), nullable=False)
    version = Column(String(64), nullable=False)
    platform = Column(String(32), nullable=False)
    architecture = Column(String(32), nullable=False)
    channel = Column(String(32), nullable=False)
    min_supported_version = Column(String(64), nullable=False)
    download_url = Column(Text)
    release_notes = Column(Text)
    published_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_active = Column(Boolean, nullable=False, server_default='false')


class MapAlias(Database.Base):
    __tablename__ = 'where_am_i_map_aliases'
    alias = Column(String(256), primary_key=True)
    map_slug = Column(String(32), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default='true')
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VersionCheckRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    product: Literal['where-am-i']
    current_version: str = Field(strict=True, max_length=64)
    platform: Literal['windows']
    architecture: Literal['x64']
    channel: Literal['stable']

    @field_validator('current_version')
    @classmethod
    def validate_version(cls, value):
        version_parts(value)
        return value


class DesktopMetadataService:
    @staticmethod
    def check_version(request):
        with Database.SessionLocal() as session:
            releases = list(session.scalars(select(DesktopRelease).where(
                DesktopRelease.product == request.product,
                DesktopRelease.platform == request.platform,
                DesktopRelease.architecture == request.architecture,
                DesktopRelease.channel == request.channel,
                DesktopRelease.is_active.is_(True), DesktopRelease.published_at <= func.now(),
            )))
            if not releases:
                raise HTTPException(404, 'DESKTOP_RELEASE_NOT_FOUND')
            latest = max(releases, key=lambda release: (
                version_parts(release.version), release.published_at, release.id))
            latest_parts = version_parts(latest.version)
            min_parts = version_parts(latest.min_supported_version)
            current_parts = version_parts(request.current_version)
            if min_parts > latest_parts:
                raise ValueError('Minimum version exceeds latest')
            if latest.release_notes is not None and len(latest.release_notes) > 4000:
                raise ValueError('Invalid release notes')
            if latest.download_url:
                validate_download_url(latest.download_url)
            if current_parts < latest_parts and not latest.download_url:
                raise ValueError('Update has no download URL')
            return {'current_version': request.current_version, 'latest_version': latest.version,
                    'min_supported_version': latest.min_supported_version,
                    'update_available': current_parts < latest_parts,
                    'update_required': current_parts < min_parts,
                    'download_url': latest.download_url, 'release_notes': latest.release_notes}

    @staticmethod
    def map_aliases():
        with Database.SessionLocal() as session:
            rows = list(session.scalars(select(MapAlias).where(MapAlias.is_active.is_(True)).limit(1025)))
            if not rows:
                raise HTTPException(404, 'MAP_ALIASES_NOT_FOUND')
            if len(rows) > 1024:
                raise ValueError('Too many active aliases')
            aliases = []
            seen = set()
            for row in rows:
                alias = normalize_alias(row.alias)
                if alias in seen:
                    raise ValueError('Duplicate map alias')
                seen.add(alias)
                aliases.append({'alias': alias, 'map': row.map_slug})
            aliases.sort(key=lambda entry: entry['alias'])
            digest = hashlib.sha256(json.dumps(aliases, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            return {'version': 'sha256:' + digest, 'aliases': aliases}


def metadata_error(error):
    if isinstance(error, ValueError):
        logger.warning('Desktop metadata unavailable (ValueError): %s', str(error))
    else:
        # SQL errors can contain bound parameters; keep those out of logs.
        logger.warning('Desktop metadata unavailable (%s)', type(error).__name__)
    raise HTTPException(503, 'DESKTOP_METADATA_UNAVAILABLE') from None


@router.post('/v3/check-version')
def check_version(request: VersionCheckRequest, response: Response):
    response.headers['Cache-Control'] = 'no-store'
    try:
        data = DesktopMetadataService.check_version(request)
    except (SQLAlchemyError, ValueError, TypeError) as error:
        metadata_error(error)
    return CustomResponse.response(data, HTTPCode.OK, Message.SUCCESS)


@router.get('/v3/map-aliases')
def map_aliases(response: Response):
    response.headers['Cache-Control'] = 'no-store'
    try:
        data = DesktopMetadataService.map_aliases()
    except (SQLAlchemyError, ValueError, TypeError) as error:
        metadata_error(error)
    return CustomResponse.response(data, HTTPCode.OK, Message.SUCCESS)
