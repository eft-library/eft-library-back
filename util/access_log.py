"""Keep access logs useful by omitting successful CORS preflight requests."""
import logging
import re


class AccessLogFilter(logging.Filter):
    options_response = re.compile(r' - "OPTIONS [^"]+" (\d{3}) - ')

    def filter(self, record):
        if record.levelno != logging.INFO:
            return True
        match = self.options_response.search(record.getMessage())
        return match is None or int(match.group(1)) >= 400


def configure_access_logging():
    logger = logging.getLogger('api.access')
    if not any(isinstance(item, AccessLogFilter) for item in logger.filters):
        logger.addFilter(AccessLogFilter())
