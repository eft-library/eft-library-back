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

    # 초기 알림 전송
    existing_notifications = await redis.lrange(f"notifications:{user_email}", 0, 9)
    # Redis에는 문자열로 저장되어 있으므로 JSON.parse 필요
    initial_notifications = [json.loads(n) for n in existing_notifications]
    await websocket.send_text(
        json.dumps({"type": "init", "notifications": initial_notifications})
    )

    # 이미 listener가 없을 때만 생성
    if user_email not in user_listeners:
        user_listeners[user_email] = asyncio.create_task(redis_listener(user_email))

    try:
        while True:
            # 클라이언트에서 메시지 수신(예: ping용)
            await websocket.receive_text()
    except Exception:
        # 연결 종료 시 cleanup
        connected_websockets.pop(user_email, None)

        # listener 취소
        if user_email in user_listeners:
            user_listeners[user_email].cancel()
            await user_listeners.pop(user_email, None)

        # 전송 기록 초기화
        if user_email in sent_notifications:
            sent_notifications.pop(user_email, None)


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

            # Redis에서 발행된 문자열을 dict로 변환
            data = json.loads(message["data"])
            notification_id = data.get("id")

            # 이미 보낸 알림이면 건너뛰기
            if notification_id in sent_notifications[user_email]:
                continue

            sent_notifications[user_email].add(notification_id)

            # WebSocket 연결이 있는 경우에만 전송
            ws = connected_websockets.get(user_email)
            if ws:
                try:
                    await ws.send_text(json.dumps({"type": "message", "data": data}))
                except Exception:
                    # 연결 끊기면 cleanup
                    connected_websockets.pop(user_email, None)
                    sent_notifications.pop(user_email, None)
                    if user_email in user_listeners:
                        user_listeners[user_email].cancel()
                        await user_listeners.pop(user_email, None)
                    break  # listener 종료
    except asyncio.CancelledError:
        # listener task 취소 시 정상 종료
        await pubsub.unsubscribe(f"notifications_channel:{user_email}")
        await pubsub.close()
