class DashboardUtil:
    """
    clickhouse와 postgresql은 서로 파라미터 바인딩 방식이 다름
    # PostgreSQL
    ":start_date", ":end_date"

    # ClickHouse
    "{start_date}", "{end_date}"
    """

    @staticmethod
    def get_psql_top_request():
        return """
            SELECT
              REQUEST,
              LINK,
              COUNT(*) AS request_count
            FROM USER_FOOTPRINT
            WHERE EXECUTE_TIME BETWEEN :start_date AND :end_date
            AND link not like '%health%'    
            GROUP BY REQUEST, LINK
            ORDER BY request_count DESC
            LIMIT 10
        """

    @staticmethod
    def get_psql_total_count():
        return """
            WITH current_period AS (
              SELECT COUNT(*) AS request_count
              FROM USER_FOOTPRINT
              WHERE FOOTPRINT_TIME >= :start_date
                AND FOOTPRINT_TIME < :end_date
            ),
            previous_period AS (
              SELECT COUNT(*) AS request_count
              FROM USER_FOOTPRINT
              WHERE FOOTPRINT_TIME >= :prev_start_date
                AND FOOTPRINT_TIME < :prev_end_date
            )
            SELECT 
              c.request_count AS current_requests,
              p.request_count AS previous_requests,
              COALESCE(
                ROUND(((c.request_count - p.request_count) * 100.0 / NULLIF(p.request_count, 0)), 1),
                0
              ) AS percent_change
            FROM current_period c, previous_period p
        """

    @staticmethod
    def get_psql_user_total_count():
        return """
            SELECT COUNT(*) AS user_total_count
            FROM USER_INFO
        """

    @staticmethod
    def get_psql_active_user_count():
        return """
            SELECT COUNT(*) AS active_user
            FROM USER_INFO
            WHERE attendance_time BETWEEN :start_date AND :end_date
        """

    @staticmethod
    def get_psql_time_distribution():
        return """
            SELECT
              TO_CHAR(
                date_trunc('hour', EXECUTE_TIME) + 
                INTERVAL '1 minute' * (FLOOR(EXTRACT(MINUTE FROM EXECUTE_TIME) / 15) * 15),
                'HH24:MI'
              ) AS time,
              COUNT(*) AS requests
            FROM USER_FOOTPRINT
            WHERE EXECUTE_TIME BETWEEN :start_date AND :end_date
            GROUP BY time
            ORDER BY time
        """

    @staticmethod
    def get_clickhouse_top_request():
        return """
            SELECT
              request,
              link,
              COUNT(*) AS request_count
            FROM prd.user_footprint
            WHERE execute_time BETWEEN {start_date} AND {end_date}
            GROUP BY request, link
            ORDER BY request_count DESC
            LIMIT 10
        """

    @staticmethod
    def get_clickhouse_total_count():
        return """
            SELECT COUNT(*) AS total_requests
            FROM prd.user_footprint
            WHERE execute_time BETWEEN {start_date} AND {end_date}
        """

    @staticmethod
    def get_clickhouse_time_distribution():
        return """
            SELECT
              toHour(execute_time) AS hour,
              toMinute(execute_time) AS minute,
              COUNT(*) AS request_count
            FROM prd.user_footprint
            WHERE execute_time BETWEEN {start_date} AND {end_date}
            GROUP BY hour, minute
            ORDER BY hour, minute
        """
