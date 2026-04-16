from sqlalchemy import text
from database import V3Database
from api.dashboard.query import DashboardQueryV3
from datetime import date
import logging

logger = logging.getLogger("api.dashboard")


class DashboardServiceV3:
    @staticmethod
    def get_chart_data_v3(start_date: date, end_date: date):
        """
        V3 상위 10개 엔드포인트
        V3 시간대별 요청 분포
        """
        try:
            with V3Database.SessionLocal() as s:
                date_param = {"start_date": start_date, "end_date": end_date}

                endpoint_query = text(DashboardQueryV3.get_psql_top_request_v3())
                endpoint_result = s.execute(endpoint_query, date_param)
                endpoint = [dict(row) for row in endpoint_result.mappings()]

                time_distribution_query = text(
                    DashboardQueryV3.get_psql_time_distribution_v3()
                )
                time_distribution_result = s.execute(
                    time_distribution_query, date_param
                )
                time_distribution = [
                    dict(row) for row in time_distribution_result.mappings()
                ]

                total_request_query = text(DashboardQueryV3.get_psql_total_count_v3())
                total_request_result = s.execute(total_request_query, date_param)
                total_request = [dict(row) for row in total_request_result.mappings()]

                total_user_query = text(DashboardQueryV3.get_psql_user_total_count_v3())
                total_user_result = s.execute(total_user_query)
                total_user = [dict(row) for row in total_user_result.mappings()]

                active_user_query = text(
                    DashboardQueryV3.get_psql_active_user_count_v3()
                )
                active_user_result = s.execute(active_user_query, date_param)
                active_user = [dict(row) for row in active_user_result.mappings()]

                health_check_query = text(DashboardQueryV3.get_psql_health_check_v3())
                health_check_result = s.execute(health_check_query, date_param)
                health_check = [dict(row) for row in health_check_result.mappings()]

                response_time_query = text(DashboardQueryV3.get_response_ms_v3())
                response_time_result = s.execute(response_time_query, date_param)
                response_time = [dict(row) for row in response_time_result.mappings()]

                return {
                    "endpoint": endpoint,
                    "time_distribution": time_distribution,
                    "active_user": active_user[0] if active_user else None,
                    "total_user": total_user[0] if total_user else None,
                    "total_request": total_request[0] if total_request else None,
                    "health_check": health_check,
                    "response_time": response_time,
                }

        except Exception as e:
            logger.error(
                f"get_chart_data_v3: {start_date}, {end_date}, error: {e}",
                exc_info=True,
            )
            return None
