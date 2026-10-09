"""Keep access logs useful by omitting successful CORS preflight requests."""
import logging
import re


class AccessLogFilterV3(logging.Filter):
    options_response_v3 = re.compile(r' - "OPTIONS [^"]+" (\d{3}) - ')

    def filter(self, record):
        if record.levelno != logging.INFO:
            return True
        match = self.options_response_v3.search(record.getMessage())
        return match is None or int(match.group(1)) >= 400


def configure_access_logging_v3():
    logger = logging.getLogger('api.access')
    if not any(isinstance(item, AccessLogFilterV3) for item in logger.filters):
        logger.addFilter(AccessLogFilterV3())
