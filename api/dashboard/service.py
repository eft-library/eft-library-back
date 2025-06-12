from sqlalchemy import text
from database import DataBaseConnector
from api.dashboard.util import DashboardUtil
from datetime import date


class DashboardService:

    @staticmethod
    def get_chart_data(start_date: date, end_date: date):
        """
        상위 10개 엔드포인트
        시간대별 요청 분포
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                date_param = {"start_date": start_date, "end_date": end_date}

                endpoint_query = text(DashboardUtil.getPSQLTopRequest())
                endpoint_result = s.execute(endpoint_query, date_param)
                endpoint = [dict(row) for row in endpoint_result.mappings()]

                time_distribution_query = text(DashboardUtil.getPSQLTimeDistribution())
                time_distribution_result = s.execute(
                    time_distribution_query, date_param
                )
                time_distribution = [
                    dict(row) for row in time_distribution_result.mappings()
                ]

                return {
                    "endpoint": endpoint,
                    "time_distribution": time_distribution,
                }

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_fix_data():
        """
        총 요청수, 현재 시간 1일 대비 트래픽 양
        1일 기준 서버 상태
        1일 기준 평균 응답 시간
        1일간 활성 사용자
        총 사용자
        """
        pass
