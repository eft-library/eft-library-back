from typing import Optional
from datetime import date
from fastapi import APIRouter, Query
from api.dashboard.service import DashboardService
from api.response import CustomResponse
from util.constants import HTTPCode
from api.constants import Message

router = APIRouter(tags=["Dashboard"])


@router.get("/wipe")
def get_wipe(
    start_date: Optional[date] = Query(None), end_date: Optional[date] = Query(None)
):
    chart_data = DashboardService.get_chart_data(start_date, end_date)
    if chart_data is None:
        return CustomResponse.response(None, HTTPCode.OK, Message.CHART_NOT_FOUND)
    return CustomResponse.response(chart_data, HTTPCode.OK, Message.SUCCESS)
