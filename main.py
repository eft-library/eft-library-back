import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from api.router import api_router
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi import FastAPI
from fastapi import FastAPI, WebSocket, Query
from util.middleware import KafkaProducerMiddleware
from api.user.util import UserUtil
from util.websocket import websocket_handler

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


@app.get("/docs")
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Swagger UI",
    )


app.include_router(api_router, prefix=os.getenv("API_PREFIX"))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
