import asyncio
import os

import aioredis
from fastapi import WebSocket
from typing import Dict

redis = aioredis.from_url(f"redis://{os.getenv('REDIS_HOST')}", decode_responses=True)
connected_websockets: Dict[str, WebSocket] = {}  # user_email: websocket


async def websocket_handler(websocket: WebSocket, user_email: str):
    await websocket.accept()
    connected_websockets[user_email] = websocket

    # 사용자별 Redis 구독
    asyncio.create_task(redis_listener(user_email))

    try:
        while True:
            await websocket.receive_text()  # 클라이언트 메시지 무시
    except:
        connected_websockets.pop(user_email, None)


async def redis_listener(user_email: str):
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"notifications_channel:{user_email}")
    async for message in pubsub.listen():
        if message["type"] == "message":
            data = message["data"]
            ws = connected_websockets.get(user_email)
            if ws:
                try:
                    await ws.send_text(data)
                except:
                    connected_websockets.pop(user_email, None)
