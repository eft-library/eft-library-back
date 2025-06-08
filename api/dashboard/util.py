class DashboardUtil:

    @staticmethod
    def getTopRequest():
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
    def getTotalCount():
        return """
            SELECT COUNT(*) AS total_requests
            FROM USER_FOOTPRINT
            WHERE EXECUTE_TIME BETWEEN :start_date AND :end_date
        """

    @staticmethod
    def getTimeDistribution():
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
