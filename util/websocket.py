import asyncio
import json
import os
from typing import Dict, Set

import aioredis
from fastapi import WebSocket

# Redis 연결
redis = aioredis.from_url(f"redis://{os.getenv('REDIS_HOST')}", decode_responses=True)

# WebSocket 연결 저장
connected_websockets: Dict[str, WebSocket] = {}  # user_email -> websocket
user_listeners: Dict[str, asyncio.Task] = {}  # user_email -> listener task
sent_notifications: Dict[str, Set[str]] = (
    {}
)  # user_email -> 이미 전송된 notification id


async def websocket_handler(websocket: WebSocket, user_email: str):
    """
    클라이언트 WebSocket 연결 처리
    """
    await websocket.accept()
    connected_websockets[user_email] = websocket

    # 초기 알림 전송 (Redis에 저장된 값은 이미 json.dumps 처리됨)
    existing_notifications = await redis.lrange(f"notifications:{user_email}", 0, 9)
    await websocket.send_text(
        json.dumps({"type": "init", "notifications": existing_notifications})
    )

    # 이미 listener가 없을 때만 생성
    if user_email not in user_listeners:
        user_listeners[user_email] = asyncio.create_task(redis_listener(user_email))

    try:
        while True:
            # 클라이언트에서 메시지 수신(예: ping용)
            await websocket.receive_text()
    except Exception:
        await cleanup_user(user_email)


async def redis_listener(user_email: str):
    """
    Redis pub/sub 구독 및 실시간 알림 전송
    """
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"notifications_channel:{user_email}")

    if user_email not in sent_notifications:
        sent_notifications[user_email] = set()

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            # Redis에서 발행된 문자열 그대로 사용
            raw_data = message["data"]
            data = json.loads(raw_data)
            notification_id = data.get("id")

            # 이미 보낸 알림이면 skip
            if notification_id in sent_notifications[user_email]:
                continue

            sent_notifications[user_email].add(notification_id)

            ws = connected_websockets.get(user_email)
            if ws:
                try:
                    # 항상 JSON 문자열로 통일
                    await ws.send_text(json.dumps({"type": "message", "data": data}))
                except Exception:
                    # 연결 끊기면 cleanup
                    await cleanup_user(user_email)
                    break
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(f"notifications_channel:{user_email}")
        await pubsub.close()


async def cleanup_user(user_email: str):
    """
    특정 유저 관련 WebSocket, listener, sent_notifications 정리
    """
    connected_websockets.pop(user_email, None)

    if user_email in user_listeners:
        user_listeners[user_email].cancel()
        await user_listeners.pop(user_email, None)

    sent_notifications.pop(user_email, None)
