class DashboardQueryV3:
    @staticmethod
    def get_psql_top_request_v3():
        return """
            SELECT
              request_type,
              url,
              COUNT(*) AS request_count
            FROM user_footprint
            WHERE (request_time AT TIME ZONE 'Asia/Seoul') >= :start_date
              AND (request_time AT TIME ZONE 'Asia/Seoul') < :end_date
              AND url NOT LIKE '%health%'
            GROUP BY request_type, url
            ORDER BY request_count DESC
            LIMIT 10
        """

    @staticmethod
    def get_psql_total_count_v3():
        return """
            SELECT COUNT(*) AS current_requests
            FROM user_footprint
            WHERE (request_time AT TIME ZONE 'Asia/Seoul') >= :start_date
              AND (request_time AT TIME ZONE 'Asia/Seoul') < :end_date
        """

    @staticmethod
    def get_psql_user_total_count_v3():
        return """
            SELECT COUNT(*) AS user_total_count
            FROM user_info
        """

    @staticmethod
    def get_psql_active_user_count_v3():
        return """
            SELECT COUNT(*) AS active_user
            FROM user_info
            WHERE (attendance_time AT TIME ZONE 'Asia/Seoul') >= :start_date
              AND (attendance_time AT TIME ZONE 'Asia/Seoul') < :end_date
        """

    @staticmethod
    def get_psql_time_distribution_v3():
        return """
            SELECT
              TO_CHAR(
                date_trunc('hour', request_time AT TIME ZONE 'Asia/Seoul') +
                INTERVAL '1 minute' * (FLOOR(EXTRACT(MINUTE FROM request_time AT TIME ZONE 'Asia/Seoul') / 15) * 15),
                'YYYY-MM-DD HH24:MI'
              ) AS time,
              COUNT(*) AS requests
            FROM user_footprint
            WHERE (request_time AT TIME ZONE 'Asia/Seoul') >= :start_date
              AND (request_time AT TIME ZONE 'Asia/Seoul') < :end_date
            GROUP BY time
            ORDER BY time
        """

    @staticmethod
    def get_psql_health_check_v3():
        return """
        SELECT
            service_name,
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'OK' THEN 1 ELSE 0 END) AS ok_count,
            SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS fail_count,
            ROUND(SUM(CASE WHEN status = 'OK' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) AS ok_percentage,
            ROUND(SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) AS fail_percentage
        FROM health_check
        WHERE (checked_time AT TIME ZONE 'Asia/Seoul') >= :start_date
          AND (checked_time AT TIME ZONE 'Asia/Seoul') < :end_date
        GROUP BY service_name
        ORDER BY service_name
        """

    @staticmethod
    def get_response_ms_v3():
        return """
        SELECT
            service_name,
            ROUND(AVG(response_ms::DOUBLE PRECISION) * 1000) AS avg_response_ms
        FROM response_time
        WHERE (checked_time AT TIME ZONE 'Asia/Seoul') >= :start_date
          AND (checked_time AT TIME ZONE 'Asia/Seoul') < :end_date
          AND response_ms IS NOT NULL
        GROUP BY service_name
        """
