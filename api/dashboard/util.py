class DashboardUtil:
    """
    clickhouse와 postgresql은 서로 파라미터 바인딩 방식이 다름
    # PostgreSQL
    ":start_date", ":end_date"

    # ClickHouse
    "{start_date}", "{end_date}"
    """

    @staticmethod
    def getPSQLTopRequest():
        return """
            SELECT
              REQUEST,
              LINK,
              COUNT(*) AS request_count
            FROM USER_FOOTPRINT
            WHERE EXECUTE_TIME BETWEEN :start_date AND :end_date
            GROUP BY REQUEST, LINK
            ORDER BY request_count DESC
            LIMIT 10
        """

    @staticmethod
    def getPSQLTotalCount():
        return """
            SELECT COUNT(*) AS total_requests
            FROM USER_FOOTPRINT
            WHERE EXECUTE_TIME BETWEEN :start_date AND :end_date
        """

    @staticmethod
    def getPSQLTimeDistribution():
        return """
            SELECT
              EXTRACT(HOUR FROM EXECUTE_TIME) AS hour,
              EXTRACT(MINUTE FROM EXECUTE_TIME) AS minute,
              COUNT(*) AS request_count
            FROM USER_FOOTPRINT
            WHERE EXECUTE_TIME BETWEEN :start_date AND :end_date
            GROUP BY hour, minute
            ORDER BY hour, minute
        """

    @staticmethod
    def getClickHouseTopRequest():
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
    def getClickHouseTotalCount():
        return """
            SELECT COUNT(*) AS total_requests
            FROM prd.user_footprint
            WHERE execute_time BETWEEN {start_date} AND {end_date}
        """

    @staticmethod
    def getClickHouseTimeDistribution():
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
