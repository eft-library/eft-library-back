import asyncio
import json
import os
import logging
from typing import Dict, Set
from redis.asyncio import Redis
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState

logger = logging.getLogger("websocket")

# Redis 연결
redis = Redis.from_url(
    f"redis://{os.getenv('REDIS_HOST')}",
    decode_responses=True,
)

# 연결 관리
connected_websockets: Dict[str, WebSocket] = {}  # user_email -> websocket
user_listeners: Dict[str, asyncio.Task] = {}  # user_email -> redis listener task
sent_notifications: Dict[str, Set[str]] = {}  # user_email -> sent notification keys


async def websocket_handler(websocket: WebSocket, user_email: str):
    """
    클라이언트 WebSocket 연결 처리
    """
    await websocket.accept()

    # 같은 유저의 기존 연결이 있으면 정리
    old_ws = connected_websockets.get(user_email)
    if old_ws and old_ws.client_state == WebSocketState.CONNECTED:
        try:
            await old_ws.close()
        except Exception:
            pass

    connected_websockets[user_email] = websocket

    try:
        # 1) 초기 알림 전달
        existing_notifications = []
        while True:
            n = await redis.lpop(f"notifications:{user_email}")
            if not n:
                break
            existing_notifications.append(json.loads(n))

        existing_notifications.reverse()

        await websocket.send_text(
            json.dumps(
                {
                    "type": "init",
                    "notifications": existing_notifications,
                }
            )
        )

        # 2) Redis listener 생성
        if user_email not in user_listeners:
            user_listeners[user_email] = asyncio.create_task(redis_listener(user_email))

        # 3) 수신 루프 (ping 용)
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        # 정상 종료 (브라우저 닫힘 / 새로고침)
        logger.info(f"WebSocket disconnected: {user_email}")

    except Exception as e:
        # 진짜 예외만 로그
        logger.exception(f"WebSocket error ({user_email})")

    finally:
        await cleanup_user(user_email)


async def redis_listener(user_email: str):
    """
    Redis Pub/Sub 구독 및 실시간 알림 전송
    """
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"notifications_channel:{user_email}")

    sent_notifications.setdefault(user_email, set())

    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue

            data = json.loads(message["data"])

            # 고유 키 (중복 방지)
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

            ws = connected_websockets.get(user_email)
            if not ws or ws.client_state != WebSocketState.CONNECTED:
                break

            try:
                await ws.send_text(
                    json.dumps(
                        {
                            "type": "message",
                            "data": data,
                        }
                    )
                )
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.exception(f"Send error ({user_email}) : {e}")
                break

    except asyncio.CancelledError:
        pass

    finally:
        try:
            await pubsub.unsubscribe(f"notifications_channel:{user_email}")
        finally:
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
    if not ws or ws.client_state != WebSocketState.CONNECTED:
        return  # 유실 허용 정책

    try:
        await ws.send_text(
            json.dumps(
                {
                    "type": "wpf_location",
                    "payload": location,
                }
            )
        )
    except WebSocketDisconnect:
        await cleanup_user(user_email)
    except Exception as e:
        logger.exception(f"WPF send error ({user_email}) {e}")
        await cleanup_user(user_email)
