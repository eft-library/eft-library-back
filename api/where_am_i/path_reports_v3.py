"""Anonymous desktop path observations; never interprets or opens reported paths."""
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, Identity, String, Text, func
from sqlalchemy.exc import SQLAlchemyError

from api.constants import Message
from api.response import CustomResponse
from database import V3Database
from util.constants import HTTPCode
from .analytics_v3 import DesktopAnalyticsRouteV3

logger_v3 = logging.getLogger('api.where_am_i.path_reports_v3')
router_v3 = APIRouter(route_class=DesktopAnalyticsRouteV3)


class PathReportRequestV3(BaseModel):
    model_config = ConfigDict(extra='forbid')
    path_type: Literal['screenshot', 'log']
    path: str = Field(strict=True, min_length=1, max_length=4096)
    app_version: str = Field(strict=True, min_length=1, max_length=64)

    @field_validator('path', 'app_version')
    @classmethod
    def validate_text_v3(cls, value):
        if not value.strip():
            raise ValueError('Must not be blank')
        if any(ord(character_v3) < 32 or ord(character_v3) == 127 for character_v3 in value):
            raise ValueError('Control characters are not allowed')
        return value  # Preserve Windows drive letters, separators, case and Unicode.


class PathReportV3(V3Database.Base):
    __tablename__ = 'where_am_i_path_reports'
    __table_args__ = (
        CheckConstraint("path_type IN ('screenshot', 'log')", name='ck_path_reports_type'),
        CheckConstraint("char_length(btrim(path)) > 0 AND char_length(path) <= 4096",
                        name='ck_path_reports_path'),
        CheckConstraint("char_length(btrim(app_version)) > 0 AND char_length(app_version) <= 64",
                        name='ck_path_reports_version'),
    )
    id = Column(BigInteger, Identity(), primary_key=True)
    path_type = Column(String(16), nullable=False)
    path = Column(Text, nullable=False)
    app_version = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PathReportServiceV3:
    @staticmethod
    def create_path_report_v3(report_v3: PathReportRequestV3):
        with V3Database.SessionLocal.begin() as session_v3:
            session_v3.add(PathReportV3(**report_v3.model_dump()))
        return True


@router_v3.post('/v3/path-reports')
def create_path_report_v3(report_v3: PathReportRequestV3):
    try:
        result_v3 = PathReportServiceV3.create_path_report_v3(report_v3)
    except SQLAlchemyError as error_v3:
        # Database exceptions may embed bound parameters (including private paths).
        logger_v3.warning('Path report storage unavailable (%s)', type(error_v3).__name__)
        raise HTTPException(status_code=503, detail='PATH_REPORT_STORAGE_UNAVAILABLE') from None
    return CustomResponse.response(result_v3, HTTPCode.OK, Message.SUCCESS)
