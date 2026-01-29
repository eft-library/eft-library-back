import json
from datetime import datetime
from zoneinfo import ZoneInfo
from starlette.middleware.base import BaseHTTPMiddleware
from util.kafka_producer import produce_message


class KafkaProducerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
        footprint_time = now_kst.isoformat()

        # 실제 클라이언트 IP 추출
        real_ip = (
            request.headers.get("CF-Connecting-IP")  # Cloudflare
            or request.headers.get("X-Real-IP")  # Nginx
            or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.client.host
            if request.client
            else "unknown"
        )

        data = {
            "method": request.method,
            "link": request.url.path,
            "footprint_time": footprint_time,
            # "client_ip": real_ip,  # IP 추가
        }
        print(real_ip)
        json_str = json.dumps(data)
        produce_message(json_str)

        response = await call_next(request)
        for header in ("x-frame-options", "X-Frame-Options"):
            if header in response.headers:
                del response.headers[header]

        return response
