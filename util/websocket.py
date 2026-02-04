import asyncio
import json
import os
from typing import Dict, Set
from redis.asyncio import Redis
from fastapi import WebSocket

# Redis 연결
redis = Redis.from_url(f"redis://{os.getenv('REDIS_HOST')}", decode_responses=True)

# WebSocket 연결 저장
connected_websockets: Dict[str, WebSocket] = {}  # user_email -> websocket
user_listeners: Dict[str, asyncio.Task] = {}  # user_email -> listener task
sent_notifications: Dict[str, Set[str]] = {}  # user_email -> 전송한 알림 고유 키


async def websocket_handler(websocket: WebSocket, user_email: str):
    """
    클라이언트 WebSocket 연결 처리
    """
    await websocket.accept()
    connected_websockets[user_email] = websocket

    # 초기 알림 가져오기 + 제거
    existing_notifications = []
    while True:
        n = await redis.lpop(f"notifications:{user_email}")
        if not n:
            break
        existing_notifications.append(json.loads(n))  # Redis에는 json.dumps로 저장됨

    # 최신 순서대로 전달
    existing_notifications.reverse()

    await websocket.send_text(
        json.dumps({"type": "init", "notifications": existing_notifications})
    )

    # listener 생성 (없으면)
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
    Redis Pub/Sub 구독 및 실시간 알림 전송
    """
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"notifications_channel:{user_email}")

    if user_email not in sent_notifications:
        sent_notifications[user_email] = set()

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            raw_data = message["data"]
            data = json.loads(raw_data)

            # 고유 키 생성 (중복 방지)
            notification_key = f"{data['noti_type']}_{data.get('post_id')}_{data.get('parent_comment_id')}_{data.get('author_email')}_{data.get('id')}"

            if notification_key in sent_notifications[user_email]:
                continue

            sent_notifications[user_email].add(notification_key)

            ws = connected_websockets.get(user_email)
            if ws:
                try:
                    # 항상 JSON 문자열로 통일
                    await ws.send_text(json.dumps({"type": "message", "data": data}))
                except Exception:
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


async def send_wpf_data_ws_direct(user_email: str, location: str):
    """
    WPF 용 WebSocket 데이터 전달
    """
    ws = connected_websockets.get(user_email)
    if not ws:
        return  # 유실 OK 정책

    try:
        await ws.send_text(
            json.dumps(
                {
                    "type": "wpf_location",
                    "payload": location,
                }
            )
        )
    except Exception:
        await cleanup_user(user_email)