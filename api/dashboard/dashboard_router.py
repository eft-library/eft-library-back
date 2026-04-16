from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Query
from api.dashboard.service import DashboardServiceV3
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Dashboard"])


@router.get("/v3/analysis")
def get_analysis_v3(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    chart_data = DashboardServiceV3.get_chart_data_v3(start_date, end_date)
    if chart_data is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.FAIL)
    return CustomResponse.response(chart_data, HTTPCode.OK, Message.SUCCESS)
