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
from pydantic import ValidationError
from redis.exceptions import ConnectionError as RedisConnectionError

from api.live_map.party.models import PartyMember, PartyRoom
from api.live_map.party.realtime_schemas import PartyHeartbeat, PartyPosition, PartyViewMap
from api.map.models import Map
from api.live_map.models import LiveMapFloor
from api.live_map.party.router import router
from api.live_map.party.realtime_service import PartyRealtimeService
from api.live_map.party.realtime_store import PartyRealtimeStore
from tests.test_live_map_party import PartyApiFixture


class PartyRealtimeFixture(PartyApiFixture):
    def create_redis(self):
        self.fake_server = fakeredis.FakeServer()
        self.redis = fakeredis.FakeRedis(server=self.fake_server, decode_responses=True)

    def create_subscriber(self):
        return fakeredis.FakeAsyncRedis(server=self.fake_server, decode_responses=True)

    def setUp(self):
        super().setUp()
        self.create_redis()
        self.addCleanup(self.redis.close)
        self.store = PartyRealtimeStore(self.redis)
        self.realtime = PartyRealtimeService(self.store)
        # Exercise the real REST post-commit publishing path.
        self.publish_patch.stop()
        for target in (
            "api.live_map.party.router.get_party_realtime_store",
            "api.live_map.party.realtime_service.get_party_realtime_store",
        ):
            patcher = patch(target, return_value=self.store)
            patcher.start()
            self.addCleanup(patcher.stop)
        subscriber_patch = patch(
            "api.live_map.party.websocket.create_party_subscriber",
            side_effect=self.create_subscriber,
        )
        subscriber_patch.start()
        self.addCleanup(subscriber_patch.stop)

        def authenticate(credentials):
            if credentials.credentials not in ("owner-token", "member-token", "other-token", "outsider-token"):
                raise HTTPException(401, "INVALID_TOKEN")
            return credentials.credentials.replace("-token", "@example.test")

        auth_patch = patch("api.live_map.party.websocket.authenticate_party_user", side_effect=authenticate)
        auth_patch.start()
        self.addCleanup(auth_patch.stop)

    @contextmanager
    def socket(self, room_id, user="owner"):
        with self.client.websocket_connect(self.base + f"/{room_id}/ws") as websocket:
            websocket.send_json({"type": "auth", "token": f"{user}-token"})
            yield websocket

    def receive(self, websocket, predicate):
        # Bound test receives, including when a regression drops the expected message.
        async def receive_with_timeout():
            with anyio.fail_after(4):
                return await websocket._send_rx.receive()

        for _ in range(30):
            message = websocket.portal.call(receive_with_timeout)
            if message["type"] == "websocket.close":
                raise WebSocketDisconnect(message["code"])
            event = json.loads(message["text"])
            if predicate(event):
                return event
        self.fail("Expected WebSocket event not received")

    def snapshot(self, websocket, predicate=lambda event: True):
        return self.receive(websocket, lambda event: event["type"] == "snapshot" and predicate(event))

    def connect_service(self, room_id, user="owner"):
        return self.realtime.connect(UUID(room_id), f"{user}@example.test", str(uuid4()))[0]

    def age_member(self, connection, seconds=91):
        self.redis.hset(
            self.store.key(connection.room_id, "last-seen"),
            f"{connection.member_id}:{connection.epoch}", time.time() - seconds,
        )


class PartyRealtimeTest(PartyRealtimeFixture):
    def test_other_map_marker_create_delete_snapshot(self):
        room_id = self.create()["room"]["id"]
        self.join(room_id)
        with self.socket(room_id, "member") as member:
            self.snapshot(member)
            response = self.marker(room_id, map_id="map-b", floor_id="floor-b")
            self.assertEqual(response.status_code, 201)
            marker = response.json()["data"]
            snapshot = self.snapshot(member, lambda e: bool(e["data"]["markers"]))
            self.assertEqual(snapshot["data"]["markers"][0]["map_id"], "map-b")
            self.assertEqual(self.request("DELETE", f"/{room_id}/markers/{marker['id']}", params={"version": 1}).status_code, 200)
            self.snapshot(member, lambda e: not e["data"]["markers"])

    def test_view_map_broadcast_snapshot_and_position_independence(self):
        room_id = self.create()["room"]["id"]
        self.join(room_id)
        with self.sessions.begin() as session:
            map_data = session.get(Map, "map-b")
            floor = session.get(LiveMapFloor, "floor-b")
            map_data.name_ko, map_data.name_en, map_data.name_ja = "지도", "Map", "マップ"
            floor.name_ko, floor.name_en, floor.name_ja = "층", "Floor", "階"
        with self.socket(room_id) as owner, self.socket(room_id, "member") as member:
            self.snapshot(owner)
            self.snapshot(member)
            owner.send_json({"type": "position", "floor_id": "floor-a", "x": 1, "z": 2})
            self.receive(member, lambda e: e["type"] == "position")
            owner.send_json({"type": "view_map", "map_id": "map-b", "floor_id": "floor-b"})
            for socket in (owner, member):
                event = self.receive(socket, lambda e: e["type"] == "view_map")
                self.assertEqual(event["data"]["map"]["name_ja"], "マップ")
                self.assertEqual(event["data"]["floor"]["name_en"], "Floor")
            member.send_json({"type": "sync"})
            snapshot = self.snapshot(member, lambda e: e["data"]["reason"] == "sync")["data"]
            self.assertEqual(snapshot["view_maps"][0]["data"]["map_id"], "map-b")
            self.assertEqual(snapshot["positions"][0]["data"]["map_id"], "map-a")
        with self.socket(room_id) as owner:
            self.assertEqual(self.snapshot(owner)["data"]["view_maps"][0]["data"]["floor_id"], "floor-b")

    def test_view_map_validation_replacement_and_membership(self):
        room_id = self.create()["room"]["id"]
        owner = self.connect_service(room_id)
        for map_id, floor_id in (("missing", "floor-a"), ("map-a", "floor-b")):
            with self.assertRaises(HTTPException) as error:
                self.realtime.message(owner, PartyViewMap(type="view_map", map_id=map_id, floor_id=floor_id))
            self.assertEqual(error.exception.status_code, 422)
        for map_id, floor_id in (("map-a", "floor-child"), ("map-b", "floor-b")):
            self.realtime.message(owner, PartyViewMap(type="view_map", map_id=map_id, floor_id=floor_id))
        events = self.realtime.refresh(owner)["data"]["view_maps"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["data"]["map_id"], "map-b")
        self.assertEqual(self.store.view_maps(room_id, {str(owner.member_id): "new-epoch"}), [])
        self.assertEqual(self.redis.hlen(self.store.key(room_id, "view-maps")), 0)
        self.request("POST", f"/{room_id}/leave")
        with self.assertRaises(HTTPException):
            self.realtime.message(owner, PartyViewMap(type="view_map", map_id="map-a", floor_id="floor-a"))

    def test_position_explicit_map_allows_other_map_without_view_change(self):
        room_id = self.create()["room"]["id"]
        owner = self.connect_service(room_id)
        self.realtime.message(owner, PartyPosition(
            type="position", map_id="map-b", floor_id="floor-b", x=1, z=2, yaw=90,
        ))
        snapshot = self.realtime.refresh(owner)["data"]
        self.assertEqual(snapshot["positions"][0]["data"]["map_id"], "map-b")
        self.assertEqual(snapshot["view_maps"], [])
        with self.assertRaises(HTTPException):
            self.realtime.message(owner, PartyPosition(
                type="position", map_id="map-b", floor_id="floor-a", x=1, z=2,
            ))

    def test_position_yaw_broadcast_and_unknown_direction(self):
        room_id = self.create()["room"]["id"]
        self.join(room_id)
        with self.socket(room_id) as owner, self.socket(room_id, "member") as member:
            self.snapshot(owner)
            self.snapshot(member)
            for extra in ({"yaw": 270.5}, {}):
                owner.send_json({"type": "position", "floor_id": "floor-a", "x": 1, "z": 2, **extra})
                for socket in (owner, member):
                    event = self.receive(socket, lambda e: e["type"] == "position")
                    self.assertEqual(event["data"].get("yaw"), extra.get("yaw"))

    def test_persistent_position_survives_time_and_is_replaced(self):
        room_id = self.create()["room"]["id"]
        owner = self.connect_service(room_id)
        self.realtime.message(owner, PartyPosition(
            type="position", floor_id="floor-a", x=1, z=2, yaw=90, persistent=True,
        ))
        epochs = {str(owner.member_id): owner.epoch}
        with patch("api.live_map.party.realtime_store.time.time", return_value=time.time() + 3600):
            positions = self.store.positions(room_id, epochs)
            self.assertEqual(len(positions), 1)
            self.assertIsNone(positions[0]["data"]["expires_at"])
            self.assertIsNotNone(self.realtime.forward(owner, positions[0]))
        restored = self.realtime.refresh(owner)["data"]["positions"]
        self.assertEqual(restored[0]["data"]["yaw"], 90)
        self.realtime.message(owner, PartyPosition(
            type="position", floor_id="floor-a", x=3, z=4, yaw=180, persistent=True,
        ))
        positions = self.store.positions(room_id, epochs)
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]["data"]["x"], 3)
        self.assertEqual(self.store.positions(room_id, {}), [])

    def test_position_yaw_validation(self):
        body = {"type": "position", "floor_id": "floor-a", "x": 1, "z": 2}
        self.assertIsNone(PartyPosition(**body).yaw)
        for yaw in (0, 90, 359.99):
            self.assertEqual(PartyPosition(**body, yaw=yaw).yaw, yaw)
        for yaw in (-1, 360, float("nan"), float("inf")):
            with self.assertRaises(ValidationError):
                PartyPosition(**body, yaw=yaw)


    def test_cleanup_lifespan_starts_and_stops_through_nested_routers(self):
        started, stopped = threading.Event(), threading.Event()

        async def cleanup_worker():
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()

        parent = APIRouter()
        parent.include_router(router, prefix="/live-map")
        app = FastAPI()
        app.include_router(parent, prefix="/api")
        with patch.dict("os.environ", {"PARTY_CLEANUP_ENABLED": "true"}):
            with patch("api.live_map.party.lifecycle.cleanup_loop", side_effect=cleanup_worker):
                with TestClient(app):
                    self.assertTrue(started.wait(timeout=2))
                self.assertTrue(stopped.wait(timeout=2))

    def test_socket_requires_auth_and_existing_membership(self):
        room_id = self.create()["room"]["id"]
        for user, status in (("bad", 401), ("outsider", 403)):
            with self.socket(room_id, user) as websocket:
                error = self.receive(websocket, lambda event: event["type"] == "error")
                self.assertEqual(error["status"], status)
                self.assertNotIn(f"{user}-token", json.dumps(error))
        with self.socket(room_id) as websocket:
            snapshot = self.snapshot(websocket)
            self.assertEqual(snapshot["data"]["presence"]["online_count"], 1)
            self.assertNotIn("@example.test", json.dumps(snapshot))
            self.assertNotIn("password", json.dumps(snapshot))

    def test_two_clients_receive_ping_and_persisted_marker_changes(self):
        room_id = self.create()["room"]["id"]
        self.join(room_id)
        with self.socket(room_id) as owner, self.socket(room_id, "member") as member:
            self.snapshot(owner)
            self.snapshot(member)
            owner.send_json({"type": "ping", "floor_id": "floor-child", "x": 1.5, "z": -2, "request_id": "ping-1"})
            for socket in (owner, member):
                ping = self.receive(socket, lambda event: event["type"] == "ping")
                self.assertEqual(ping["data"]["request_id"], "ping-1")
                self.assertGreater(ping["data"]["expires_at"], time.time() + 55)
                self.assertLessEqual(ping["data"]["expires_at"], time.time() + 60)
            marker = self.marker(room_id).json()["data"]
            snapshot = self.snapshot(member, lambda e: any(m["id"] == marker["id"] for m in e["data"]["markers"]))
            self.assertEqual(snapshot["data"]["presence"]["online_count"], 2)
            update = self.request("PUT", f"/{room_id}/markers/{marker['id']}", json={
                "floor_id": "floor-a", "x": 9, "z": 10, "version": 1,
            })
            self.assertEqual(update.status_code, 200)
            self.snapshot(member, lambda e: any(m["version"] == 2 for m in e["data"]["markers"]))
            self.request("DELETE", f"/{room_id}/markers/{marker['id']}", params={"version": 2})
            self.snapshot(member, lambda e: not e["data"]["markers"])

    def test_kick_and_room_close_disconnect_sockets(self):
        room_id = self.create()["room"]["id"]
        member_id = self.join(room_id).json()["data"]["me"]["id"]
        with self.socket(room_id, "member") as member:
            self.snapshot(member)
            self.request("POST", f"/{room_id}/members/{member_id}/kick")
            error = self.receive(member, lambda e: e["type"] == "error")
            self.assertEqual(error["status"], 403)
            with self.assertRaises(WebSocketDisconnect) as disconnected:
                self.receive(member, lambda e: True)
            self.assertEqual(disconnected.exception.code, 4403)
        with self.socket(room_id) as owner:
            self.snapshot(owner)
            self.request("DELETE", f"/{room_id}")
            error = self.receive(owner, lambda e: e["type"] == "error")
            self.assertEqual(error["msg"], "ROOM_CLOSED")
            with self.assertRaises(WebSocketDisconnect) as disconnected:
                self.receive(owner, lambda e: True)
            self.assertEqual(disconnected.exception.code, 4410)

    def test_reconnect_restores_positions_and_heartbeat_reconciles_missed_notification(self):
        room_id = self.create()["room"]["id"]
        with self.socket(room_id) as owner:
            self.snapshot(owner)
            owner.send_json({"type": "position", "floor_id": "floor-a", "x": 7, "z": 8, "yaw": 123.5})
            event = self.receive(owner, lambda e: e["type"] == "position")
            self.assertEqual(event["data"]["yaw"], 123.5)
        with self.socket(room_id) as owner:
            snapshot = self.snapshot(owner)
            self.assertEqual(snapshot["data"]["positions"][0]["data"]["x"], 7)
            self.assertEqual(snapshot["data"]["positions"][0]["data"]["yaw"], 123.5)
            with patch.object(self.store, "changed", side_effect=RedisConnectionError("down")):
                response = self.marker(room_id)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.headers["X-Party-Realtime"], "unavailable")
            owner.send_json({"type": "heartbeat"})
            snapshot = self.snapshot(owner, lambda e: e["data"]["reason"] == "heartbeat")
            self.assertEqual(len(snapshot["data"]["markers"]), 1)

    def test_invalid_floor_and_spoofed_member_are_not_published(self):
        room_id = self.create()["room"]["id"]
        with self.socket(room_id) as owner:
            self.snapshot(owner)
            owner.send_json({"type": "ping", "floor_id": "floor-b", "x": 1, "z": 2})
            error = self.receive(owner, lambda e: e["type"] == "error")
            self.assertEqual(error["msg"], "FLOOR_NOT_IN_ROOM_MAP")
            owner.send_json({"type": "position", "floor_id": "floor-a", "x": 1, "z": 2, "member_id": str(uuid4())})
            error = self.receive(owner, lambda e: e["type"] == "error")
            self.assertEqual(error["msg"], "INVALID_MESSAGE")
            owner.send_json({"type": "heartbeat"})
            self.snapshot(owner, lambda e: e["data"]["reason"] == "heartbeat")
            self.assertEqual(self.redis.hlen(self.store.key(room_id, "positions")), 0)

    def test_multiple_tabs_count_once_and_cleanup_transfers_owner(self):
        room_id = self.create()["room"]["id"]
        self.join(room_id)
        owner = self.connect_service(room_id)
        owner_tab = self.connect_service(room_id)
        member = self.connect_service(room_id, "member")
        self.assertEqual(self.realtime.refresh(owner)["data"]["presence"]["online_count"], 2)
        self.realtime.disconnect(owner_tab)
        self.assertEqual(self.realtime.refresh(owner)["data"]["presence"]["online_count"], 2)
        self.realtime.disconnect(owner)
        self.assertFalse(self.realtime.cleanup_room(UUID(room_id)))
        self.age_member(owner)
        self.assertTrue(self.realtime.cleanup_room(UUID(room_id)))
        snapshot = self.realtime.refresh(member)
        self.assertEqual(snapshot["data"]["me"]["role"], "owner")
        self.assertEqual(snapshot["data"]["room"]["member_count"], 1)
        self.realtime.disconnect(member)
        self.age_member(member)
        self.assertTrue(self.realtime.cleanup_room(UUID(room_id)))
        self.assertEqual(self.request("GET", f"/{room_id}").status_code, 410)

    def test_old_socket_cannot_resume_after_leave_and_rejoin(self):
        room_id = self.create()["room"]["id"]
        self.join(room_id)
        old = self.connect_service(room_id, "member")
        self.realtime.message(old, PartyPosition(type="position", floor_id="floor-a", x=1, z=2))
        self.request("POST", f"/{room_id}/leave", user="member")
        self.join(room_id)
        with self.assertRaises(HTTPException) as result:
            self.realtime.message(old, PartyHeartbeat(type="heartbeat"))
        self.assertEqual(result.exception.detail, "PARTY_MEMBERSHIP_CHANGED")
        new = self.connect_service(room_id, "member")
        self.assertEqual(self.realtime.refresh(new)["data"]["positions"], [])
        self.realtime.disconnect(old)
        self.assertEqual(self.realtime.refresh(new)["data"]["presence"]["online_count"], 1)

    def test_redis_outage_does_not_evict_and_restart_grants_grace(self):
        room_id = self.create()["room"]["id"]
        owner = self.connect_service(room_id)
        self.realtime.disconnect(owner)
        self.age_member(owner)
        self.fake_server.connected = False
        with self.assertRaises(RedisConnectionError):
            self.realtime.cleanup_room(UUID(room_id))
        with self.sessions() as session:
            self.assertIsNone(session.get(PartyRoom, UUID(room_id)).closed_at)
            self.assertEqual(session.get(PartyMember, owner.member_id).status, "joined")
        self.fake_server.connected = True
        self.redis.flushall()
        self.assertFalse(self.realtime.cleanup_room(UUID(room_id)))

    def test_room_isolation_expiry_and_connection_limit(self):
        room_id = self.create()["room"]["id"]
        owner = self.connect_service(room_id)
        for _ in range(4):
            self.connect_service(room_id)
        with self.assertRaises(HTTPException) as result:
            self.connect_service(room_id)
        self.assertEqual(result.exception.detail, "TOO_MANY_PARTY_CONNECTIONS")
        self.realtime.message(owner, PartyPosition(type="position", floor_id="floor-a", x=1, z=2))
        event = self.realtime.refresh(owner)["data"]["positions"][0]
        self.assertIsNone(self.realtime.forward(owner, {**event, "room_id": str(uuid4())}))
        event["data"]["expires_at"] = time.time() - 1
        self.assertIsNone(self.realtime.forward(owner, event))
        self.store.save_position(room_id, str(owner.member_id), owner.epoch, event)
        self.assertEqual(self.realtime.refresh(owner)["data"]["positions"], [])

    def test_socket_size_limit(self):
        room_id = self.create()["room"]["id"]
        with self.socket(room_id) as owner:
            self.snapshot(owner)
            owner.send_text("x" * 8193)
            error = self.receive(owner, lambda e: e["type"] == "error")
            self.assertEqual(error["msg"], "MESSAGE_TOO_LARGE")
            with self.assertRaises(WebSocketDisconnect) as disconnected:
                self.receive(owner, lambda e: True)
            self.assertEqual(disconnected.exception.code, 1009)


if __name__ == "__main__":
    unittest.main()
