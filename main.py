import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from starlette.responses import PlainTextResponse
from api.router import api_router
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi import FastAPI, WebSocket, Query
from util.middleware import KafkaProducerMiddleware
from api.user.util import UserUtil
from util.websocket import websocket_handler
import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger("api.access")  # 커스텀 로거 사용

logging.getLogger("uvicorn.access").disabled = True

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

app.add_middleware(KafkaProducerMiddleware)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    로그인한 사용자만 WebSocket 연결
    토큰은 query param으로 전달
    """
    user_email = UserUtil.verify_google_token(token)
    if not user_email:
        await websocket.close(code=1008)  # 정책 위반
        return

    await websocket_handler(websocket, user_email)


@app.get(
    "/",
    include_in_schema=False,
)
def root():
    return {"status": "ok"}


@app.get(
    "/docs",
    include_in_schema=False,
)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Swagger UI",
    )


@app.get(
    "/health",
    include_in_schema=False,
)
def health_check():
    return {"status": "ok"}


@app.get(
    "/robots.txt",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
def robots_txt():
    return """User-agent: *
Sitemap: https://eftlibrary.com/sitemap/main.xml
Sitemap: https://eftlibrary.com/sitemap/boss.xml
Sitemap: https://eftlibrary.com/sitemap/quest.xml
Sitemap: https://eftlibrary.com/sitemap/legal.xml
Sitemap: https://eftlibrary.com/sitemap/information.xml
Sitemap: https://eftlibrary.com/sitemap/map.xml
Sitemap: https://eftlibrary.com/sitemap/item.xml
Sitemap: https://eftlibrary.com/sitemap/features.xml

#DaumWebMasterTool:f9f3c352224a2c2a460baed45afaad021ca93fb7f26302959c7b4441d6f411da:KwfSfnXgL1bn4FKLKNMlhA==
"""


@app.get(
    "/.well-known/security.txt",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
def security_txt():
    return "Contact: mailto:poeynus@gmail.com\n" "Expires: 2030-12-31T23:59:59Z\n"


app.include_router(api_router, prefix=os.getenv("API_PREFIX"))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
