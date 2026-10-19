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
from database import V3Database
from util.constants import HTTPCode
from .desktop_contract_v3 import MAP_SLUGS_V3, normalize_alias_v3, validate_download_url_v3, version_parts_v3

logger_v3 = logging.getLogger('api.where_am_i.metadata_v3')
router_v3 = APIRouter()


class DesktopReleaseV3(V3Database.Base):
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


class MapAliasV3(V3Database.Base):
    __tablename__ = 'where_am_i_map_aliases'
    alias = Column(String(256), primary_key=True)
    map_slug = Column(String(32), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default='true')
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VersionCheckRequestV3(BaseModel):
    model_config = ConfigDict(extra='forbid')
    product: Literal['where-am-i']
    current_version: str = Field(strict=True, max_length=64)
    platform: Literal['windows']
    architecture: Literal['x64']
    channel: Literal['stable']

    @field_validator('current_version')
    @classmethod
    def validate_version_v3(cls, value):
        version_parts_v3(value)
        return value


class DesktopMetadataServiceV3:
    @staticmethod
    def check_version_v3(request_v3):
        with V3Database.SessionLocal() as session_v3:
            releases_v3 = list(session_v3.scalars(select(DesktopReleaseV3).where(
                DesktopReleaseV3.product == request_v3.product,
                DesktopReleaseV3.platform == request_v3.platform,
                DesktopReleaseV3.architecture == request_v3.architecture,
                DesktopReleaseV3.channel == request_v3.channel,
                DesktopReleaseV3.is_active.is_(True), DesktopReleaseV3.published_at <= func.now(),
            )))
            if not releases_v3:
                raise HTTPException(404, 'DESKTOP_RELEASE_NOT_FOUND')
            latest_v3 = max(releases_v3, key=lambda release_v3: (
                version_parts_v3(release_v3.version), release_v3.published_at, release_v3.id))
            latest_parts_v3 = version_parts_v3(latest_v3.version)
            min_parts_v3 = version_parts_v3(latest_v3.min_supported_version)
            current_parts_v3 = version_parts_v3(request_v3.current_version)
            if min_parts_v3 > latest_parts_v3:
                raise ValueError('Minimum version exceeds latest')
            if latest_v3.release_notes is not None and len(latest_v3.release_notes) > 4000:
                raise ValueError('Invalid release notes')
            if latest_v3.download_url:
                validate_download_url_v3(latest_v3.download_url)
            if current_parts_v3 < latest_parts_v3 and not latest_v3.download_url:
                raise ValueError('Update has no download URL')
            return {'current_version': request_v3.current_version, 'latest_version': latest_v3.version,
                    'min_supported_version': latest_v3.min_supported_version,
                    'update_available': current_parts_v3 < latest_parts_v3,
                    'update_required': current_parts_v3 < min_parts_v3,
                    'download_url': latest_v3.download_url, 'release_notes': latest_v3.release_notes}

    @staticmethod
    def map_aliases_v3():
        with V3Database.SessionLocal() as session_v3:
            rows_v3 = list(session_v3.scalars(select(MapAliasV3).where(MapAliasV3.is_active.is_(True)).limit(1025)))
            if not rows_v3:
                raise HTTPException(404, 'MAP_ALIASES_NOT_FOUND')
            if len(rows_v3) > 1024:
                raise ValueError('Too many active aliases')
            aliases_v3 = []
            seen_v3 = set()
            for row_v3 in rows_v3:
                alias_v3 = normalize_alias_v3(row_v3.alias)
                if row_v3.map_slug not in MAP_SLUGS_V3 or alias_v3 in seen_v3:
                    raise ValueError('Invalid or duplicate map alias')
                seen_v3.add(alias_v3)
                aliases_v3.append({'alias': alias_v3, 'map': row_v3.map_slug})
            aliases_v3.sort(key=lambda entry_v3: entry_v3['alias'])
            digest_v3 = hashlib.sha256(json.dumps(aliases_v3, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            return {'version': 'sha256:' + digest_v3, 'aliases': aliases_v3}


def metadata_error_v3(error_v3):
    if isinstance(error_v3, ValueError):
        logger_v3.warning('Desktop metadata unavailable (ValueError): %s', str(error_v3))
    else:
        # SQL errors can contain bound parameters; keep those out of logs.
        logger_v3.warning('Desktop metadata unavailable (%s)', type(error_v3).__name__)
    raise HTTPException(503, 'DESKTOP_METADATA_UNAVAILABLE') from None


@router_v3.post('/v3/check-version')
def check_version_v3(request_v3: VersionCheckRequestV3, response: Response):
    response.headers['Cache-Control'] = 'no-store'
    try:
        data_v3 = DesktopMetadataServiceV3.check_version_v3(request_v3)
    except (SQLAlchemyError, ValueError, TypeError) as error_v3:
        metadata_error_v3(error_v3)
    return CustomResponse.response(data_v3, HTTPCode.OK, Message.SUCCESS)


@router_v3.get('/v3/map-aliases')
def map_aliases_v3(response: Response):
    response.headers['Cache-Control'] = 'no-store'
    try:
        data_v3 = DesktopMetadataServiceV3.map_aliases_v3()
    except (SQLAlchemyError, ValueError, TypeError) as error_v3:
        metadata_error_v3(error_v3)
    return CustomResponse.response(data_v3, HTTPCode.OK, Message.SUCCESS)
