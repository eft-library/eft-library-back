import json
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from api.router import api_router
from fastapi.openapi.docs import get_swagger_ui_html
from kafka_producer import produce_message
from fastapi import FastAPI, Request
from datetime import datetime
from zoneinfo import ZoneInfo
import json

load_dotenv()

app = FastAPI(title="eft-library-back")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def kafka_producer_middleware(request: Request, call_next):
    # 기존 Kafka 메시지 생산 로직
    now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
    footprint_time = now_kst.isoformat()
    data = {
        "method": request.method,
        "link": request.url.path,
        "footprint_time": footprint_time,
    }
    json_str = json.dumps(data)
    produce_message(json_str)

    # 요청 처리 후 응답 가져오기
    response = await call_next(request)

    # iframe 허용을 위해 x-frame-options 헤더 제거 또는 변경
    if "x-frame-options" in response.headers:
        del response.headers["x-frame-options"]
    if "X-Frame-Options" in response.headers:
        del response.headers["X-Frame-Options"]

    return response


@app.get("/docs")
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Swagger UI",
    )


app.include_router(api_router, prefix=os.getenv("API_PREFIX"))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
