import asyncio
import json
import os

import aioredis
from fastapi import WebSocket
from typing import Dict

redis = aioredis.from_url(f"redis://{os.getenv('REDIS_HOST')}", decode_responses=True)
connected_websockets: Dict[str, WebSocket] = {}  # user_email: websocket


user_listeners: dict[str, asyncio.Task] = {}


async def websocket_handler(websocket: WebSocket, user_email: str):
    await websocket.accept()
    connected_websockets[user_email] = websocket

    # 기존 알림 전송
    existing_notifications = await redis.lrange(f"notifications:{user_email}", 0, 9)
    await websocket.send_text(
        json.dumps({"type": "init", "notifications": existing_notifications})
    )

    # 이미 listener가 없을 때만 생성
    if user_email not in user_listeners:
        user_listeners[user_email] = asyncio.create_task(redis_listener(user_email))

    try:
        while True:
            await websocket.receive_text()
    except:
        connected_websockets.pop(user_email, None)
        # websocket 연결 끊기면 listener도 취소
        if user_email in user_listeners:
            user_listeners[user_email].cancel()
            await user_listeners.pop(user_email, None)


sent_notifications: dict[str, set] = {}


async def redis_listener(user_email: str):
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"notifications_channel:{user_email}")

    if user_email not in sent_notifications:
        sent_notifications[user_email] = set()

    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            notification_id = data.get("id")

            # 이미 보낸 알림이면 skip
            if notification_id in sent_notifications[user_email]:
                continue

            sent_notifications[user_email].add(notification_id)

            ws = connected_websockets.get(user_email)
            if ws:
                try:
                    await ws.send_text(json.dumps({"type": "message", "data": data}))
                except:
                    connected_websockets.pop(user_email, None)
