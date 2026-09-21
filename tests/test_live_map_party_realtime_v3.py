"""Isolated WebSocket/Redis protocol tests; requires fakeredis[lua]."""
import json
import asyncio
import threading
import time
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from uuid import UUID, uuid4

import anyio
import fakeredis
from fastapi import APIRouter, FastAPI, HTTPException, WebSocketDisconnect
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError

from api.live_map.party_v3.models import PartyMemberV3, PartyRoomV3
from api.live_map.party_v3.realtime_schemas import PartyHeartbeatV3, PartyPositionV3
from api.live_map.party_v3.router import router_v3
from api.live_map.party_v3.realtime_service import PartyRealtimeServiceV3
from api.live_map.party_v3.realtime_store import PartyRealtimeStoreV3
from tests.test_live_map_party_v3 import PartyApiFixtureV3


class PartyRealtimeFixtureV3(PartyApiFixtureV3):
    def create_redis_v3(self):
        self.fake_server_v3 = fakeredis.FakeServer()
        self.redis_v3 = fakeredis.FakeRedis(server=self.fake_server_v3, decode_responses=True)

    def create_subscriber_v3(self):
        return fakeredis.FakeAsyncRedis(server=self.fake_server_v3, decode_responses=True)

    def setUp(self):
        super().setUp()
        self.create_redis_v3()
        self.addCleanup(self.redis_v3.close)
        self.store_v3 = PartyRealtimeStoreV3(self.redis_v3)
        self.realtime_v3 = PartyRealtimeServiceV3(self.store_v3)
        # Exercise the real REST post-commit publishing path.
        self.publish_patch_v3.stop()
        for target in (
            "api.live_map.party_v3.router.get_party_realtime_store_v3",
            "api.live_map.party_v3.realtime_service.get_party_realtime_store_v3",
        ):
            patcher = patch(target, return_value=self.store_v3)
            patcher.start()
            self.addCleanup(patcher.stop)
        subscriber_patch = patch(
            "api.live_map.party_v3.websocket.create_party_subscriber_v3",
            side_effect=self.create_subscriber_v3,
        )
        subscriber_patch.start()
        self.addCleanup(subscriber_patch.stop)

        def authenticate_v3(credentials):
            if credentials.credentials not in ("owner-token", "member-token", "other-token", "outsider-token"):
                raise HTTPException(401, "INVALID_TOKEN")
            return credentials.credentials.replace("-token", "@example.test")

        auth_patch = patch("api.live_map.party_v3.websocket.authenticate_party_user_v3", side_effect=authenticate_v3)
        auth_patch.start()
        self.addCleanup(auth_patch.stop)

    @contextmanager
    def socket_v3(self, room_id, user="owner"):
        with self.client_v3.websocket_connect(self.base_v3 + f"/{room_id}/ws") as websocket:
            websocket.send_json({"type": "auth", "token": f"{user}-token"})
            yield websocket

    def receive_v3(self, websocket, predicate):
        # Bound test receives, including when a regression drops the expected message.
        async def receive_with_timeout_v3():
            with anyio.fail_after(4):
                return await websocket._send_rx.receive()

        for _ in range(30):
            message = websocket.portal.call(receive_with_timeout_v3)
            if message["type"] == "websocket.close":
                raise WebSocketDisconnect(message["code"])
            event = json.loads(message["text"])
            if predicate(event):
                return event
        self.fail("Expected WebSocket event not received")

    def snapshot_v3(self, websocket, predicate=lambda event: True):
        return self.receive_v3(websocket, lambda event: event["type"] == "snapshot" and predicate(event))

    def connect_service_v3(self, room_id, user="owner"):
        return self.realtime_v3.connect_v3(UUID(room_id), f"{user}@example.test", str(uuid4()))[0]

    def age_member_v3(self, connection, seconds=91):
        self.redis_v3.hset(
            self.store_v3.key_v3(connection.room_id, "last-seen"),
            f"{connection.member_id}:{connection.epoch}", time.time() - seconds,
        )


class PartyRealtimeTestV3(PartyRealtimeFixtureV3):
    def test_cleanup_lifespan_starts_and_stops_through_nested_routers_v3(self):
        started, stopped = threading.Event(), threading.Event()

        async def cleanup_worker_v3():
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()

        parent = APIRouter()
        parent.include_router(router_v3, prefix="/live-map")
        app = FastAPI()
        app.include_router(parent, prefix="/api")
        with patch.dict("os.environ", {"PARTY_CLEANUP_ENABLED": "true"}):
            with patch("api.live_map.party_v3.lifecycle.cleanup_loop_v3", side_effect=cleanup_worker_v3):
                with TestClient(app):
                    self.assertTrue(started.wait(timeout=2))
                self.assertTrue(stopped.wait(timeout=2))

    def test_socket_requires_auth_and_existing_membership_v3(self):
        room_id = self.create_v3()["room"]["id"]
        for user, status in (("bad", 401), ("outsider", 403)):
            with self.socket_v3(room_id, user) as websocket:
                error = self.receive_v3(websocket, lambda event: event["type"] == "error")
                self.assertEqual(error["status"], status)
                self.assertNotIn(f"{user}-token", json.dumps(error))
        with self.socket_v3(room_id) as websocket:
            snapshot = self.snapshot_v3(websocket)
            self.assertEqual(snapshot["data"]["presence"]["online_count"], 1)
            self.assertNotIn("@example.test", json.dumps(snapshot))
            self.assertNotIn("password", json.dumps(snapshot))

    def test_two_clients_receive_ping_and_persisted_marker_changes_v3(self):
        room_id = self.create_v3()["room"]["id"]
        self.join_v3(room_id)
        with self.socket_v3(room_id) as owner, self.socket_v3(room_id, "member") as member:
            self.snapshot_v3(owner)
            self.snapshot_v3(member)
            owner.send_json({"type": "ping", "floor_id": "floor-child", "x": 1.5, "z": -2, "request_id": "ping-1"})
            for socket in (owner, member):
                ping = self.receive_v3(socket, lambda event: event["type"] == "ping")
                self.assertEqual(ping["data"]["request_id"], "ping-1")
                self.assertGreater(ping["data"]["expires_at"], time.time())
            marker = self.marker_v3(room_id).json()["data"]
            snapshot = self.snapshot_v3(member, lambda e: any(m["id"] == marker["id"] for m in e["data"]["markers"]))
            self.assertEqual(snapshot["data"]["presence"]["online_count"], 2)
            update = self.request_v3("PUT", f"/{room_id}/markers/{marker['id']}", json={
                "floor_id": "floor-a", "x": 9, "z": 10, "version": 1,
            })
            self.assertEqual(update.status_code, 200)
            self.snapshot_v3(member, lambda e: any(m["version"] == 2 for m in e["data"]["markers"]))
            self.request_v3("DELETE", f"/{room_id}/markers/{marker['id']}", params={"version": 2})
            self.snapshot_v3(member, lambda e: not e["data"]["markers"])

    def test_kick_and_room_close_disconnect_sockets_v3(self):
        room_id = self.create_v3()["room"]["id"]
        member_id = self.join_v3(room_id).json()["data"]["me"]["id"]
        with self.socket_v3(room_id, "member") as member:
            self.snapshot_v3(member)
            self.request_v3("POST", f"/{room_id}/members/{member_id}/kick")
            error = self.receive_v3(member, lambda e: e["type"] == "error")
            self.assertEqual(error["status"], 403)
            with self.assertRaises(WebSocketDisconnect) as disconnected:
                self.receive_v3(member, lambda e: True)
            self.assertEqual(disconnected.exception.code, 4403)
        with self.socket_v3(room_id) as owner:
            self.snapshot_v3(owner)
            self.request_v3("DELETE", f"/{room_id}")
            error = self.receive_v3(owner, lambda e: e["type"] == "error")
            self.assertEqual(error["msg"], "ROOM_CLOSED")
            with self.assertRaises(WebSocketDisconnect) as disconnected:
                self.receive_v3(owner, lambda e: True)
            self.assertEqual(disconnected.exception.code, 4410)

    def test_reconnect_restores_positions_and_heartbeat_reconciles_missed_notification_v3(self):
        room_id = self.create_v3()["room"]["id"]
        with self.socket_v3(room_id) as owner:
            self.snapshot_v3(owner)
            owner.send_json({"type": "position", "floor_id": "floor-a", "x": 7, "z": 8})
            self.receive_v3(owner, lambda e: e["type"] == "position")
        with self.socket_v3(room_id) as owner:
            snapshot = self.snapshot_v3(owner)
            self.assertEqual(snapshot["data"]["positions"][0]["data"]["x"], 7)
            with patch.object(self.store_v3, "changed_v3", side_effect=RedisConnectionError("down")):
                response = self.marker_v3(room_id)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.headers["X-Party-Realtime"], "unavailable")
            owner.send_json({"type": "heartbeat"})
            snapshot = self.snapshot_v3(owner, lambda e: e["data"]["reason"] == "heartbeat")
            self.assertEqual(len(snapshot["data"]["markers"]), 1)

    def test_invalid_floor_and_spoofed_member_are_not_published_v3(self):
        room_id = self.create_v3()["room"]["id"]
        with self.socket_v3(room_id) as owner:
            self.snapshot_v3(owner)
            owner.send_json({"type": "ping", "floor_id": "floor-b", "x": 1, "z": 2})
            error = self.receive_v3(owner, lambda e: e["type"] == "error")
            self.assertEqual(error["msg"], "FLOOR_NOT_IN_ROOM_MAP")
            owner.send_json({"type": "position", "floor_id": "floor-a", "x": 1, "z": 2, "member_id": str(uuid4())})
            error = self.receive_v3(owner, lambda e: e["type"] == "error")
            self.assertEqual(error["msg"], "INVALID_MESSAGE")
            owner.send_json({"type": "heartbeat"})
            self.snapshot_v3(owner, lambda e: e["data"]["reason"] == "heartbeat")
            self.assertEqual(self.redis_v3.hlen(self.store_v3.key_v3(room_id, "positions")), 0)

    def test_multiple_tabs_count_once_and_cleanup_transfers_owner_v3(self):
        room_id = self.create_v3()["room"]["id"]
        self.join_v3(room_id)
        owner = self.connect_service_v3(room_id)
        owner_tab = self.connect_service_v3(room_id)
        member = self.connect_service_v3(room_id, "member")
        self.assertEqual(self.realtime_v3.refresh_v3(owner)["data"]["presence"]["online_count"], 2)
        self.realtime_v3.disconnect_v3(owner_tab)
        self.assertEqual(self.realtime_v3.refresh_v3(owner)["data"]["presence"]["online_count"], 2)
        self.realtime_v3.disconnect_v3(owner)
        self.assertFalse(self.realtime_v3.cleanup_room_v3(UUID(room_id)))
        self.age_member_v3(owner)
        self.assertTrue(self.realtime_v3.cleanup_room_v3(UUID(room_id)))
        snapshot = self.realtime_v3.refresh_v3(member)
        self.assertEqual(snapshot["data"]["me"]["role"], "owner")
        self.assertEqual(snapshot["data"]["room"]["member_count"], 1)
        self.realtime_v3.disconnect_v3(member)
        self.age_member_v3(member)
        self.assertTrue(self.realtime_v3.cleanup_room_v3(UUID(room_id)))
        self.assertEqual(self.request_v3("GET", f"/{room_id}").status_code, 410)

    def test_old_socket_cannot_resume_after_leave_and_rejoin_v3(self):
        room_id = self.create_v3()["room"]["id"]
        self.join_v3(room_id)
        old = self.connect_service_v3(room_id, "member")
        self.realtime_v3.message_v3(old, PartyPositionV3(type="position", floor_id="floor-a", x=1, z=2))
        self.request_v3("POST", f"/{room_id}/leave", user="member")
        self.join_v3(room_id)
        with self.assertRaises(HTTPException) as result:
            self.realtime_v3.message_v3(old, PartyHeartbeatV3(type="heartbeat"))
        self.assertEqual(result.exception.detail, "PARTY_MEMBERSHIP_CHANGED")
        new = self.connect_service_v3(room_id, "member")
        self.assertEqual(self.realtime_v3.refresh_v3(new)["data"]["positions"], [])
        self.realtime_v3.disconnect_v3(old)
        self.assertEqual(self.realtime_v3.refresh_v3(new)["data"]["presence"]["online_count"], 1)

    def test_redis_outage_does_not_evict_and_restart_grants_grace_v3(self):
        room_id = self.create_v3()["room"]["id"]
        owner = self.connect_service_v3(room_id)
        self.realtime_v3.disconnect_v3(owner)
        self.age_member_v3(owner)
        self.fake_server_v3.connected = False
        with self.assertRaises(RedisConnectionError):
            self.realtime_v3.cleanup_room_v3(UUID(room_id))
        with self.sessions_v3() as session:
            self.assertIsNone(session.get(PartyRoomV3, UUID(room_id)).closed_at)
            self.assertEqual(session.get(PartyMemberV3, owner.member_id).status, "joined")
        self.fake_server_v3.connected = True
        self.redis_v3.flushall()
        self.assertFalse(self.realtime_v3.cleanup_room_v3(UUID(room_id)))

    def test_room_isolation_expiry_and_connection_limit_v3(self):
        room_id = self.create_v3()["room"]["id"]
        owner = self.connect_service_v3(room_id)
        for _ in range(4):
            self.connect_service_v3(room_id)
        with self.assertRaises(HTTPException) as result:
            self.connect_service_v3(room_id)
        self.assertEqual(result.exception.detail, "TOO_MANY_PARTY_CONNECTIONS")
        self.realtime_v3.message_v3(owner, PartyPositionV3(type="position", floor_id="floor-a", x=1, z=2))
        event = self.realtime_v3.refresh_v3(owner)["data"]["positions"][0]
        self.assertIsNone(self.realtime_v3.forward_v3(owner, {**event, "room_id": str(uuid4())}))
        event["data"]["expires_at"] = time.time() - 1
        self.assertIsNone(self.realtime_v3.forward_v3(owner, event))
        self.store_v3.save_position_v3(room_id, str(owner.member_id), owner.epoch, event)
        self.assertEqual(self.realtime_v3.refresh_v3(owner)["data"]["positions"], [])

    def test_socket_size_limit_v3(self):
        room_id = self.create_v3()["room"]["id"]
        with self.socket_v3(room_id) as owner:
            self.snapshot_v3(owner)
            owner.send_text("x" * 8193)
            error = self.receive_v3(owner, lambda e: e["type"] == "error")
            self.assertEqual(error["msg"], "MESSAGE_TOO_LARGE")
            with self.assertRaises(WebSocketDisconnect) as disconnected:
                self.receive_v3(owner, lambda e: True)
            self.assertEqual(disconnected.exception.code, 1009)


if __name__ == "__main__":
    unittest.main()
