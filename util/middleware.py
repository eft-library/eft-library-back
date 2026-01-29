import json
from datetime import datetime
from zoneinfo import ZoneInfo
from starlette.middleware.base import BaseHTTPMiddleware
from util.kafka_producer import produce_message
import logging
import time
from dotenv import load_dotenv
import os

logger = logging.getLogger("api.access")

load_dotenv()


class KafkaProducerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()  # 시작 시간 기록

        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
        footprint_time = now_kst.isoformat()

        real_ip = (
            request.headers.get("cf-connecting-ip")
            or request.headers.get("x-real-ip")
            or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.client.host
            if request.client
            else "unknown"
        )

        data = {
            "method": request.method,
            "link": request.url.path,
            "footprint_time": footprint_time,
            "client_ip": real_ip,
        }
        json_str = json.dumps(data)
        produce_message(json_str)

        response = await call_next(request)

        # 처리 시간 계산
        process_time = time.time() - start_time

        # 로그 (처리 시간 추가)
        if real_ip != os.getenv("IP"):
            logger.info(
                f'{real_ip} - "{request.method} {request.url.path}" '
                f"{response.status_code} - {process_time:.3f}s"
            )

        for header in ("x-frame-options", "X-Frame-Options"):
            if header in response.headers:
                del response.headers[header]

        return response
