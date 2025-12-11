# import json
# from datetime import datetime
# from zoneinfo import ZoneInfo
# from starlette.middleware.base import BaseHTTPMiddleware
# from util.kafka_producer import produce_message
#
#
# class KafkaProducerMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request, call_next):
#         now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
#         footprint_time = now_kst.isoformat()
#         data = {
#             "method": request.method,
#             "link": request.url.path,
#             "footprint_time": footprint_time,
#         }
#         json_str = json.dumps(data)
#         produce_message(json_str)
#
#         response = await call_next(request)
#
#         for header in ("x-frame-options", "X-Frame-Options"):
#             if header in response.headers:
#                 del response.headers[header]
#
#         return response
