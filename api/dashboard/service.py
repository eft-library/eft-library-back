from sqlalchemy import text
from database import DataBaseConnector
from api.dashboard.util import DashboardUtil
from datetime import date, datetime, timedelta


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

                endpoint_query = text(DashboardUtil.get_psql_top_request())
                endpoint_result = s.execute(endpoint_query, date_param)
                endpoint = [dict(row) for row in endpoint_result.mappings()]

                time_distribution_query = text(DashboardUtil.get_psql_time_distribution())
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
    def get_fix_data(start_date: date, end_date: date):
        """
        총 요청수, 현재 시간 1일 대비 트래픽 양
        1일 기준 서버 상태
        1일 기준 평균 응답 시간
        1일간 활성 사용자
        총 사용자
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                date_param = {"start_date": start_date, "end_date": end_date}

                total_request_query = text(DashboardUtil.get_psql_total_count())
                total_request_result = s.execute(total_request_query, date_param)
                total_request = [dict(row) for row in total_request_result.mappings()]

                total_user_query = text(DashboardUtil.get_psql_user_total_count())
                total_user_result = s.execute(total_user_query)
                total_user = [dict(row) for row in total_user_result.mappings()]

                active_user_query = text(DashboardUtil.get_psql_active_user_count())
                active_user_result = s.execute(active_user_query, date_param)
                active_user = [dict(row) for row in active_user_result.mappings()]

                return {"active_user": active_user, "total_user": total_user, "total_request": total_request}
        except Exception as e:
            print("오류 발생:", e)
            return None
