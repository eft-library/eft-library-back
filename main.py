from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from api.router import api_router
from fastapi.openapi.docs import get_swagger_ui_html

load_dotenv()

app = FastAPI(title="tarkov-korea-wiki-back")


# Swagger UI 제공을 위한 엔드포인트
@app.get("/docs")
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",  # FastAPI 자동 생성된 OpenAPI 스키마 경로
        title="Swagger UI",
    )


app.include_router(api_router, prefix=os.getenv("API_PREFIX"))


# React 애플리케이션의 index.html을 반환하는 라우터 추가


# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
