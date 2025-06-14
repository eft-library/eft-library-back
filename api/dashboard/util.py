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
            WHERE EXECUTE_TIME AT TIME ZONE 'Asia/Seoul' BETWEEN :start_date AND :end_date
              AND LINK NOT LIKE '%health%'
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
              WHERE FOOTPRINT_TIME AT TIME ZONE 'Asia/Seoul' >= :start_date
                AND FOOTPRINT_TIME AT TIME ZONE 'Asia/Seoul' < :end_date
            )
            SELECT 
              c.request_count AS current_requests
            FROM current_period c
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
            WHERE attendance_time AT TIME ZONE 'Asia/Seoul' BETWEEN :start_date AND :end_date
        """

    @staticmethod
    def get_psql_time_distribution():
        return """
            SELECT
              TO_CHAR(
                date_trunc('hour', EXECUTE_TIME AT TIME ZONE 'Asia/Seoul') + 
                INTERVAL '1 minute' * (FLOOR(EXTRACT(MINUTE FROM EXECUTE_TIME AT TIME ZONE 'Asia/Seoul') / 15) * 15),
                'HH24:MI'
              ) AS time,
              COUNT(*) AS requests
            FROM USER_FOOTPRINT
            WHERE EXECUTE_TIME AT TIME ZONE 'Asia/Seoul' BETWEEN :start_date AND :end_date
            GROUP BY time
            ORDER BY time
        """

    @staticmethod
    def get_psql_health_check():
        return """
        SELECT
            service_name,
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'OK' THEN 1 ELSE 0 END) AS ok_count,
            SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS fail_count,
            ROUND(SUM(CASE WHEN status = 'OK' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) AS ok_percentage,
            ROUND(SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) AS fail_percentage
        FROM health_check
        WHERE checked_time BETWEEN (:start_date AT TIME ZONE 'Asia/Seoul') AND (:end_date AT TIME ZONE 'Asia/Seoul')
        GROUP BY service_name
        ORDER BY service_name
        """

    @staticmethod
    def get_response_ms():
        return """
        SELECT
            service_name,
            ROUND(AVG(response_ms::DOUBLE PRECISION) * 1000) AS avg_response_ms
        FROM
            response_time
        WHERE
            checked_time BETWEEN (:start_date AT TIME ZONE 'Asia/Seoul') AND (:end_date AT TIME ZONE 'Asia/Seoul')
          AND response_ms IS NOT NULL
        GROUP BY
            service_name
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
