import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from starlette.middleware.base import BaseHTTPMiddleware
from util.kafka_producer import produce_message
import logging
import time
from dotenv import load_dotenv
import os
import re
from fastapi.responses import Response
from collections import defaultdict

BLOCK_EXT = re.compile(r".*\.(php|jsp|asp|exe|sh|cgi|html)$", re.IGNORECASE)
BLOCK_TRAVERSAL = re.compile(r"\.\.|\/etc\/|\/usr\/|\/var\/|\\\\|%2e%2e", re.IGNORECASE)

# 의심스러운 파라미터명 (실제 사용하는 파라미터 확인 후 조정)
SUSPICIOUS_PARAMS = {"file", "path", "include", "template", "doc"}

# 화이트리스트 경로 (필요시 추가)
SAFE_PATHS = {"/download", "/api/files"}

logger = logging.getLogger("api.access")
load_dotenv()


def get_real_ip(request) -> str:
    logger.info(dict(request.headers))
    # proxy.ts에서 심어준 헤더 우선
    if client_ip := request.headers.get("x-client-real-ip"):
        return client_ip
    return request.client.host if request.client else "unknown"


class KafkaProducerMiddleware(BaseHTTPMiddleware):
    request_counts = defaultdict(list)

    async def dispatch(self, request, call_next):
        start_time = time.time()
        path = request.url.path
        real_ip = get_real_ip(request)

        # 1. Path 검사 (항상)
        if BLOCK_EXT.search(path):
            logger.warning(f"BLOCKED (path) - {real_ip} - {request.method} {path}")
            return Response(status_code=410)

        # 2. 화이트리스트가 아닌 경우만 쿼리 검사
        if path not in SAFE_PATHS:
            # 의심스러운 파라미터만 검사
            for param_name in SUSPICIOUS_PARAMS:
                param_value = request.query_params.get(param_name, "")
                if BLOCK_EXT.search(param_value) or BLOCK_TRAVERSAL.search(param_value):
                    logger.warning(
                        f"BLOCKED (param) - {real_ip} - {request.method} {path}?"
                        f"{param_name}={param_value}"
                    )
                    return Response(status_code=410)

        # 3. 디렉토리 트래버설 검사 (전체 URL)
        full_url = str(request.url)
        if BLOCK_TRAVERSAL.search(full_url):
            logger.warning(f"BLOCKED (traversal) - {real_ip} - {full_url}")
            return Response(status_code=410)

        # Rate limiting
        now = datetime.now()
        self.request_counts[real_ip] = [
            t for t in self.request_counts[real_ip] if now - t < timedelta(minutes=1)
        ]

        if len(self.request_counts[real_ip]) > 100:
            logger.warning(f"Rate limit exceeded: {real_ip}")
            return Response(status_code=429)

        self.request_counts[real_ip].append(now)

        response = await call_next(request)
        process_time = time.time() - start_time

        # if real_ip != os.getenv("IP"):
        logger.info(
            f'{real_ip} - "{request.method} {path}" '
            f"{response.status_code} - {process_time:.3f}s"
        )
        data = {
            "method": request.method,
            "link": path,
            "footprint_time": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
        }
        produce_message(json.dumps(data))

        return response
