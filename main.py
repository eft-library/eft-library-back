from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from api.router import api_router
from starlette.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html

load_dotenv()

app = FastAPI(
    title='tarkov-korea-wiki-back',
    openapi_url=f"/api/v1/openapi.json",
    docs_url=None,
    redoc_url=None,
)

# 정적 파일 서빙 설정
app.mount("/static", StaticFiles(directory="ui/build/static"), name="static")

# React 애플리케이션의 index.html을 반환하는 라우터 추가
@app.get("/")
async def serve_react_app():
    return FileResponse("ui/build/index.html")

# Swagger UI 제공을 위한 엔드포인트
@app.get("/docs")
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url="/api/v1/openapi.json", title="Swagger UI")

app.include_router(api_router, prefix=os.getenv("API_PREFIX"))

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
