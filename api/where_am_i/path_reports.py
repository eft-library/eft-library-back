"""Anonymous desktop path observations; never interprets or opens reported paths."""
import logging
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, Identity, String, Text, func
from sqlalchemy.exc import SQLAlchemyError

from api.constants import Message
from api.response import CustomResponse
from database import Database
from util.constants import HTTPCode
from .analytics import DesktopAnalyticsRoute

from util.http_exceptions import HttpError

logger = logging.getLogger('api.where_am_i.path_reports')
router = APIRouter(route_class=DesktopAnalyticsRoute)


class PathReportRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    path_type: Literal['screenshot', 'log']
    path: str = Field(strict=True, min_length=1, max_length=4096)
    app_version: str = Field(strict=True, min_length=1, max_length=64)

    @field_validator('path', 'app_version')
    @classmethod
    def validate_text(cls, value):
        if not value.strip():
            raise ValueError('Must not be blank')
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise ValueError('Control characters are not allowed')
        return value  # Preserve Windows drive letters, separators, case and Unicode.


class PathReport(Database.Base):
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


class PathReportService:
    @staticmethod
    def create_path_report(report: PathReportRequest):
        with Database.SessionLocal.begin() as session:
            session.add(PathReport(**report.model_dump()))
        return True


@router.post('/v3/path-reports')
def create_path_report(report: PathReportRequest):
    try:
        result = PathReportService.create_path_report(report)
    except SQLAlchemyError as error:
        # Database exceptions may embed bound parameters (including private paths).
        logger.warning('Path report storage unavailable (%s)', type(error).__name__)
        raise HttpError.PATH_REPORT_STORAGE_UNAVAILABLE.exception() from None
    return CustomResponse.response(result, HTTPCode.OK, Message.SUCCESS)
