import json
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
import os
from api.router import api_router
from fastapi.openapi.docs import get_swagger_ui_html
from kafka_producer import produce_message
from fastapi import FastAPI, Request

load_dotenv()

app = FastAPI(title="eft-library-back")


@app.middleware("http")
async def kafka_producer_middleware(request: Request, call_next):
    now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
    # client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    print("X-Forwarded-For:", request.headers.get("x-forwarded-for", ""))
    footprint_time = now_kst.isoformat()
    data = {
        "method": request.method,
        "link": request.url.path,
        "footprint_time": footprint_time,
    }
    json_str = json.dumps(data)
    produce_message(json_str)
    response = await call_next(request)
    return response


@app.get("/docs")
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Swagger UI",
    )


app.include_router(api_router, prefix=os.getenv("API_PREFIX"))

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
