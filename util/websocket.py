import asyncio
import json
import os

import aioredis
from fastapi import WebSocket
from typing import Dict

redis = aioredis.from_url(f"redis://{os.getenv('REDIS_HOST')}", decode_responses=True)
connected_websockets: Dict[str, WebSocket] = {}  # user_email: websocket


async def websocket_handler(websocket: WebSocket, user_email: str):
    await websocket.accept()
    connected_websockets[user_email] = websocket

    # ✅ 기존 알림 불러오기 (예: 최근 10개)
    redis_key = f"notifications:{user_email}"
    existing_notifications = await redis.lrange(redis_key, 0, 9)
    await websocket.send_text(
        json.dumps({"type": "init", "notifications": existing_notifications})
    )

    # ✅ 실시간 알림 수신
    asyncio.create_task(redis_listener(user_email))

    try:
        while True:
            await websocket.receive_text()
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
