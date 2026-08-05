import asyncio
import json
import os
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from starlette.websockets import WebSocketState
import logging

logger = logging.getLogger("ws")

# Redis 연결
redis = Redis.from_url(
    f"redis://{os.getenv('REDIS_HOST')}",
    decode_responses=True,
)

# In-memory (worker-local)
connected_websockets: Dict[str, WebSocket] = {}  # user_email -> websocket
user_listeners: Dict[str, asyncio.Task] = {}  # user_email -> redis listener task
sent_notifications: Dict[str, Set[str]] = {}  # user_email -> dedup key set


async def safe_send_text(websocket: WebSocket, data: str):
    if websocket.client_state != WebSocketState.CONNECTED:
        return False

    try:
        await websocket.send_text(data)
        return True
    except WebSocketDisconnect:
        return False
    except RuntimeError as e:
        logger.info(f"[SEND_SKIP] WebSocket already closed: {e}")
        return False


# WebSocket Handler
async def websocket_handler(websocket: WebSocket, user_email: str):
    """
    WebSocket 연결 처리
    """
    await websocket.accept()
    connected_websockets[user_email] = websocket
    logger.info(f"[OPEN] WebSocket 연결: {user_email}")

    # 1. 밀린 알림 먼저 전달 (Redis List)
    existing_notifications = []
    while True:
        n = await redis.lpop(f"notifications:{user_email}")
        if not n:
            break
        existing_notifications.append(json.loads(n))

    existing_notifications.reverse()

    sent = await safe_send_text(
        websocket,
        json.dumps(
            {
                "type": "init",
                "notifications": existing_notifications,
            }
        ),
    )
    if not sent:
        logger.info(f"[CLOSE] WebSocket init 전송 실패: {user_email}")
        await cleanup_user(user_email)
        return

    # 2. Redis listener 시작 (없으면)
    if user_email not in user_listeners:
        user_listeners[user_email] = asyncio.create_task(redis_listener(user_email))

    try:
        # ping / keep-alive 용
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except RuntimeError as e:
        logger.info(f"[CLOSE] WebSocket receive 종료: {user_email}, {e}")
    finally:
        logger.info(f"[CLOSE] WebSocket 연결 종료: {user_email}")
        await cleanup_user(user_email)


# Redis Pub/Sub Listener
async def redis_listener(user_email: str):
    """
    Redis Pub/Sub 수신 → WebSocket 전송
    """
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"notifications_channel:{user_email}")

    sent_notifications.setdefault(user_email, set())

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            data = json.loads(message["data"])
            ws = connected_websockets.get(user_email)

            if not ws:
                # WS 없으면 그냥 소비 (유실 OK 정책)
                continue

            # WPF 위치 메시지
            if data.get("type") in {
                "wpf_location",
                "wpf_log_location",
                "wpf_raid_state",
            }:
                sent = await safe_send_text(ws, json.dumps(data))
                if not sent:
                    await cleanup_user(user_email)
                continue

            # 일반 알림 (중복 방지)
            notification_key = (
                f"{data.get('noti_type')}_"
                f"{data.get('post_id')}_"
                f"{data.get('parent_comment_id')}_"
                f"{data.get('author_email')}_"
                f"{data.get('id')}"
            )

            if notification_key in sent_notifications[user_email]:
                continue

            sent_notifications[user_email].add(notification_key)

            sent = await safe_send_text(
                ws,
                json.dumps(
                    {
                        "type": "message",
                        "data": data,
                    }
                ),
            )
            if not sent:
                await cleanup_user(user_email)

    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(f"notifications_channel:{user_email}")
        await pubsub.close()


# Cleanup
async def cleanup_user(user_email: str):
    """
    WebSocket / Listener / 메모리 정리
    """
    connected_websockets.pop(user_email, None)

    task = user_listeners.pop(user_email, None)
    if task:
        task.cancel()

    sent_notifications.pop(user_email, None)


# WPF 위치 전송 (Redis ONLY)
async def send_wpf_location(user_email: str, location: str):
    """
    WPF 위치 정보 Redis Pub/Sub 전송
    기존에는 바로 보냈었는데, worker를 추가하면서 redis 거치는 것으로 수정
    """
    await redis.publish(
        f"notifications_channel:{user_email}",
        json.dumps(
            {
                "type": "wpf_location",
                "payload": location,
            }
        ),
    )


async def send_wpf_raid_state(user_email: str, state: dict):
    """Publish the desktop app's current raid state to the signed-in web client."""
    await redis.publish(
        f"notifications_channel:{user_email}",
        json.dumps(
            {
                "type": "wpf_raid_state",
                "payload": state,
            }
        ),
    )


async def send_wpf_log_location(user_email: str, location: dict):
    """Publish a sparse location observed in an EFT application log."""
    await redis.publish(
        f"notifications_channel:{user_email}",
        json.dumps(
            {
                "type": "wpf_log_location",
                "payload": location,
            }
        ),
    )
