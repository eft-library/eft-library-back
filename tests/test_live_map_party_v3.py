"""Run: .venv/bin/python -m unittest tests.test_live_map_party_v3 -v

HTTP/service integration uses isolated SQLite, never the configured application DB.
PostgreSQL row-lock concurrency still needs a dedicated PostgreSQL integration run.
"""
import unittest
import tempfile
from unittest.mock import Mock, patch
from uuid import uuid4

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from api.live_map.models import LiveMapFloorV3
from api.live_map.party_v3.models import PartyMarkerV3, PartyMemberV3, PartyRoomV3
from api.live_map.party_v3.router import router_v3
from api.live_map.party_v3.security import (
    PartyPasswordV3, PartyRateLimiterV3, authenticate_party_user_v3,
)
from api.map.models import MapV3
from api.user.user_res_models import UserV3
from database import V3Database


class PartyApiFixtureV3(unittest.TestCase):
    def create_database_v3(self):
        self.directory_v3 = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory_v3.cleanup)
        self.engine_v3 = create_engine(
            f"sqlite:///{self.directory_v3.name}/party-test.sqlite",
            connect_args={"check_same_thread": False},
        )
        tables = [model.__table__ for model in (
            MapV3, LiveMapFloorV3, UserV3, PartyRoomV3, PartyMemberV3, PartyMarkerV3,
        )]
        V3Database.Base.metadata.create_all(self.engine_v3, tables=tables)
        # Match the partial indexes that require deliberate flush ordering on transfer.
        with self.engine_v3.begin() as connection:
            connection.exec_driver_sql("""
                CREATE UNIQUE INDEX test_owner_v3 ON live_map_party_members(room_id)
                WHERE role = 'owner' AND status = 'joined'
            """)
            connection.exec_driver_sql("""
                CREATE UNIQUE INDEX test_color_v3 ON live_map_party_members(room_id, color)
                WHERE status = 'joined'
            """)
            connection.exec_driver_sql("""
                CREATE UNIQUE INDEX test_user_v3 ON live_map_party_members(room_id, user_email)
            """)

    def setUp(self):
        self.create_database_v3()
        self.sessions_v3 = sessionmaker(self.engine_v3, autoflush=False)
        with self.sessions_v3.begin() as session:
            session.add_all([UserV3(email=f"{user}@example.test", nickname=user) for user in (
                "owner", "member", "other", "outsider",
            )])
            session.add_all([
                MapV3(id="map-a", is_use=True),
                MapV3(id="map-child", parent_map_id="map-a", is_use=True),
                MapV3(id="map-b", is_use=True),
                MapV3(id="map-empty", is_use=True),
            ])
            session.add_all([
                LiveMapFloorV3(id="floor-a", map_id="map-a"),
                LiveMapFloorV3(id="floor-child", map_id="map-child"),
                LiveMapFloorV3(id="floor-b", map_id="map-b"),
            ])

        self.limiter_v3 = Mock(spec=PartyRateLimiterV3)
        self.session_patch_v3 = patch.object(V3Database, "SessionLocal", self.sessions_v3)
        self.limiter_patch_v3 = patch(
            "api.live_map.party_v3.service.get_party_rate_limiter_v3", return_value=self.limiter_v3,
        )
        self.session_patch_v3.start()
        self.limiter_patch_v3.start()
        self.publish_patch_v3 = patch("api.live_map.party_v3.router.publish_party_change_v3", return_value=True)
        self.publish_mock_v3 = self.publish_patch_v3.start()
        self.addCleanup(self.publish_patch_v3.stop)
        self.addCleanup(self.session_patch_v3.stop)
        self.addCleanup(self.limiter_patch_v3.stop)
        self.addCleanup(self.engine_v3.dispose)
        self.app_v3 = FastAPI()
        self.app_v3.include_router(router_v3, prefix="/live-map")

        def test_identity_v3(request: Request):
            identity = request.headers.get("x-test-user")
            if identity is None:
                raise HTTPException(401, "LOGIN_REQUIRED")
            return f"{identity}@example.test"

        self.app_v3.dependency_overrides[authenticate_party_user_v3] = test_identity_v3
        self.client_v3 = TestClient(self.app_v3)
        self.addCleanup(self.client_v3.close)
        self.base_v3 = "/live-map/v3/party/rooms"

    def request_v3(self, method, path="", user="owner", **kwargs):
        headers = {} if user is None else {"x-test-user": user}
        return self.client_v3.request(method, self.base_v3 + path, headers=headers, **kwargs)

    def create_v3(self, user="owner", **changes):
        body = {"name": "우리 파티", "map_id": "map-a", "password": "secret-password"}
        body.update(changes)
        response = self.request_v3("POST", user=user, json=body)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]

    def join_v3(self, room_id, user="member", password="secret-password"):
        return self.request_v3("POST", f"/{room_id}/join", user=user, json={"password": password})

    def marker_v3(self, room_id, user="owner", **changes):
        body = {"floor_id": "floor-a", "x": 12.5, "z": -47.25, "label": "집결"}
        body.update(changes)
        return self.request_v3("POST", f"/{room_id}/markers", user=user, json=body)


class PartyApiTestV3(PartyApiFixtureV3):
    def test_marker_maps_create_update_and_snapshot_v3(self):
        room_id = self.create_v3()["room"]["id"]
        self.join_v3(room_id)
        marker = self.marker_v3(room_id, user="member", map_id="map-b", floor_id="floor-b")
        self.assertEqual(marker.status_code, 201)
        data = marker.json()["data"]
        self.assertEqual(data["map_id"], "map-b")
        self.assertEqual(self.request_v3("GET", f"/{room_id}").json()["data"]["markers"][0]["map_id"], "map-b")
        path = f"/{room_id}/markers/{data['id']}"
        body = {"floor_id": "floor-b", "x": 3, "z": 4, "version": 1}
        updated = self.request_v3("PUT", path, user="member", json=body)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["data"]["map_id"], "map-b")
        body.update(map_id="map-a", floor_id="floor-child", version=2)
        self.assertEqual(self.request_v3("PUT", path, user="member", json=body).status_code, 200)
        self.assertEqual(self.marker_v3(room_id, map_id="map-b", floor_id="floor-a").status_code, 422)
        self.assertEqual(self.marker_v3(room_id, map_id="missing").status_code, 422)
        self.assertEqual(self.request_v3("DELETE", path, user="member", params={"version": 3}).status_code, 200)
        self.assertEqual(self.request_v3("GET", f"/{room_id}/markers").json()["data"], [])

    def test_public_list_and_private_snapshot_v3(self):
        snapshot = self.create_v3()
        room_id = snapshot["room"]["id"]
        listing = self.request_v3("GET", user=None)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()["data"]["rooms"][0]["member_count"], 1)
        for secret in ("password", "scrypt-v3", "@example.test", "user_email"):
            self.assertNotIn(secret, listing.text)
            self.assertNotIn(secret, str(snapshot))
        self.assertEqual(self.request_v3("GET", f"/{room_id}", user=None).status_code, 401)
        self.assertEqual(self.request_v3("GET", f"/{room_id}", user="outsider").status_code, 403)
        self.app_v3.dependency_overrides.clear()
        self.assertEqual(self.request_v3("GET", f"/{room_id}", user=None).status_code, 401)

    def test_registered_account_and_live_map_required_v3(self):
        body = {"name": "방", "map_id": "map-a", "password": "secret-password"}
        self.assertEqual(self.request_v3("POST", user="unknown", json=body).status_code, 403)
        for map_id in ("does-not-exist", "map-empty"):
            self.assertEqual(self.request_v3("POST", json={**body, "map_id": map_id}).status_code, 422)
        self.assertEqual(self.request_v3("GET").json()["data"]["total"], 0)

    def test_password_capacity_and_idempotent_join_v3(self):
        room_id = self.create_v3(max_members=2)["room"]["id"]
        self.assertEqual(self.join_v3(room_id, password="wrong-password").status_code, 403)
        joined = self.join_v3(room_id)
        self.assertEqual(joined.status_code, 200, joined.text)
        again = self.join_v3(room_id)
        self.assertEqual(again.json()["data"]["me"]["id"], joined.json()["data"]["me"]["id"])
        self.assertEqual(again.json()["data"]["room"]["member_count"], 2)
        self.assertEqual(self.join_v3(room_id, user="other").status_code, 409)

    def test_leave_rejoin_preserves_identity_and_marker_author_v3(self):
        room_id = self.create_v3()["room"]["id"]
        member_id = self.join_v3(room_id).json()["data"]["me"]["id"]
        marker = self.marker_v3(room_id, user="member")
        self.assertEqual(marker.status_code, 201)
        self.assertEqual(self.request_v3("POST", f"/{room_id}/leave", user="member").status_code, 200)
        self.assertEqual(self.request_v3("GET", f"/{room_id}/markers", user="member").status_code, 403)
        snapshot = self.join_v3(room_id).json()["data"]
        self.assertEqual(snapshot["me"]["id"], member_id)
        self.assertEqual(snapshot["markers"][0]["created_by_member_id"], member_id)

    def test_owner_leave_transfers_then_last_leave_closes_v3(self):
        room_id = self.create_v3()["room"]["id"]
        member_id = self.join_v3(room_id).json()["data"]["me"]["id"]
        left = self.request_v3("POST", f"/{room_id}/leave")
        self.assertEqual(left.status_code, 200, left.text)
        self.assertEqual(left.json()["data"]["owner_member_id"], member_id)
        snapshot = self.request_v3("GET", f"/{room_id}", user="member").json()["data"]
        self.assertEqual(snapshot["me"]["role"], "owner")
        self.assertTrue(self.request_v3("POST", f"/{room_id}/leave", user="member").json()["data"]["closed"])
        self.assertEqual(self.request_v3("GET").json()["data"]["total"], 0)
        self.assertEqual(self.join_v3(room_id).status_code, 410)

    def test_transfer_releases_owner_unique_index_v3(self):
        room_id = self.create_v3()["room"]["id"]
        member_id = self.join_v3(room_id).json()["data"]["me"]["id"]
        response = self.request_v3("POST", f"/{room_id}/owner", json={"member_id": member_id})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["data"]["me"]["role"], "member")
        self.assertEqual(self.request_v3("DELETE", f"/{room_id}").status_code, 403)
        self.assertEqual(self.request_v3("DELETE", f"/{room_id}", user="member").status_code, 200)

    def test_kick_revokes_read_write_and_reentry_v3(self):
        room_id = self.create_v3()["room"]["id"]
        member_id = self.join_v3(room_id).json()["data"]["me"]["id"]
        response = self.request_v3("POST", f"/{room_id}/members/{member_id}/kick")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.join_v3(room_id).json()["msg"], "PARTY_MEMBER_KICKED")
        self.assertEqual(self.request_v3("GET", f"/{room_id}", user="member").status_code, 403)
        self.assertEqual(self.marker_v3(room_id, user="member").status_code, 403)

    def test_lock_password_change_and_capacity_floor_v3(self):
        room_id = self.create_v3()["room"]["id"]
        self.join_v3(room_id)
        self.assertEqual(self.request_v3("PATCH", f"/{room_id}", user="member", json={"name": "bad"}).status_code, 403)
        self.assertEqual(self.request_v3("PATCH", f"/{room_id}", json={"max_members": 1}).status_code, 409)
        self.request_v3("PATCH", f"/{room_id}", json={"is_locked": True})
        self.assertEqual(self.join_v3(room_id, user="other").json()["msg"], "ROOM_LOCKED")
        self.assertEqual(self.request_v3("GET", f"/{room_id}", user="member").status_code, 200)
        self.request_v3("PATCH", f"/{room_id}", json={"is_locked": False, "password": "new-password"})
        self.assertEqual(self.join_v3(room_id, user="other").json()["msg"], "INVALID_ROOM_PASSWORD")
        self.assertEqual(self.join_v3(room_id, user="other", password="new-password").status_code, 200)

    def test_color_normalization_and_conflict_v3(self):
        room_id = self.create_v3()["room"]["id"]
        self.join_v3(room_id)
        response = self.request_v3("PATCH", f"/{room_id}/members/me", json={"color": "#aabbcc"})
        self.assertEqual(response.json()["data"]["color"], "#AABBCC")
        response = self.request_v3("PATCH", f"/{room_id}/members/me", user="member", json={"color": "#aabbcc"})
        self.assertEqual(response.status_code, 409)

    def test_floor_membership_and_marker_permissions_v3(self):
        room_id = self.create_v3()["room"]["id"]
        self.join_v3(room_id)
        self.join_v3(room_id, user="other")
        self.assertEqual(self.marker_v3(room_id, floor_id="floor-b").status_code, 422)
        marker = self.marker_v3(room_id, user="member", floor_id="floor-child").json()["data"]
        marker_path = f"/{room_id}/markers/{marker['id']}"
        body = {"floor_id": "floor-a", "x": 1, "z": 2, "version": 1}
        self.assertEqual(self.request_v3("PUT", marker_path, user="other", json=body).status_code, 403)
        updated = self.request_v3("PUT", marker_path, json=body)
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["data"]["version"], 2)
        self.assertEqual(self.request_v3("PUT", marker_path, user="member", json=body).status_code, 409)
        self.assertEqual(self.request_v3("DELETE", marker_path, params={"version": 1}).status_code, 409)
        self.assertEqual(self.request_v3("DELETE", marker_path, user="member", params={"version": 2}).status_code, 200)
        self.assertEqual(self.request_v3("GET", f"/{room_id}/markers").json()["data"], [])

    def test_cross_room_targets_are_rejected_v3(self):
        first = self.create_v3()
        second = self.create_v3(user="other")
        room_id = first["room"]["id"]
        other_id = second["room"]["id"]
        target_id = second["me"]["id"]
        marker_id = self.marker_v3(other_id, user="other").json()["data"]["id"]
        self.assertEqual(self.request_v3("POST", f"/{room_id}/owner", json={"member_id": target_id}).status_code, 404)
        self.assertEqual(self.request_v3("POST", f"/{room_id}/members/{target_id}/kick").status_code, 404)
        self.assertEqual(self.request_v3("DELETE", f"/{room_id}/markers/{marker_id}", params={"version": 1}).status_code, 404)

    def test_search_is_literal_and_paginated_v3(self):
        self.create_v3(name="100% 파티")
        self.create_v3(name="1000 파티", map_id="map-b")
        listing = self.request_v3("GET", params={"search": "%"}).json()["data"]
        self.assertEqual(listing["total"], 1)
        self.assertEqual(listing["rooms"][0]["name"], "100% 파티")
        listing = self.request_v3("GET", params={"limit": 1, "offset": 1}).json()["data"]
        self.assertEqual(listing["total"], 2)
        self.assertEqual(len(listing["rooms"]), 1)
        self.assertEqual(self.request_v3("GET", params={"map_id": "map-b"}).json()["data"]["total"], 1)

    def test_validation_does_not_echo_password_or_allow_invalid_updates_v3(self):
        secret = "a-private-password-that-must-not-be-echoed"
        body = {"name": " ", "map_id": "map-a", "password": secret}
        response = self.request_v3("POST", json=body)
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(secret, response.text)
        room_id = self.create_v3()["room"]["id"]
        for body in ({}, {"password": None}, {"is_locked": None}, {"password": "    "}, {"max_members": 11}):
            self.assertEqual(self.request_v3("PATCH", f"/{room_id}", json=body).status_code, 422)
        self.assertEqual(self.marker_v3(room_id, x="NaN").status_code, 422)
        self.assertEqual(self.marker_v3(room_id, z="Infinity").status_code, 422)
        self.assertEqual(self.request_v3("GET", "/not-a-uuid").status_code, 422)

    def test_rate_limit_prevents_membership_and_preserves_retry_header_v3(self):
        room_id = self.create_v3()["room"]["id"]
        self.limiter_v3.consume_v3.side_effect = HTTPException(429, "TOO_MANY_ATTEMPTS", headers={"Retry-After": "60"})
        response = self.join_v3(room_id)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["Retry-After"], "60")
        self.assertEqual(self.request_v3("GET", f"/{room_id}").json()["data"]["room"]["member_count"], 1)

    def test_commit_failure_rolls_back_before_response_v3(self):
        def reject_commit_v3(session):
            raise OperationalError("sensitive SQL", {"password": "do-not-echo"}, Exception("offline"))

        event.listen(self.sessions_v3, "before_commit", reject_commit_v3)
        try:
            response = self.request_v3("POST", json={"name": "방", "map_id": "map-a", "password": "secret-password"})
        finally:
            event.remove(self.sessions_v3, "before_commit", reject_commit_v3)
        self.assertEqual(response.status_code, 503, response.text)
        self.assertNotIn("do-not-echo", response.text)
        self.publish_mock_v3.assert_not_called()
        with self.sessions_v3() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(PartyRoomV3)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(PartyMemberV3)), 0)

    def test_openapi_and_missing_entities_v3(self):
        schema = self.app_v3.openapi()
        self.assertEqual(sum(hasattr(route, "methods") for route in router_v3.routes), 14)
        self.assertIn("requestBody", schema["paths"][self.base_v3]["post"])
        self.assertEqual(self.request_v3("GET", f"/{uuid4()}").status_code, 404)


class PartySecurityTestV3(unittest.TestCase):
    def test_password_hash_salt_and_verification_v3(self):
        first = PartyPasswordV3.hash_v3("password-with-unicode-암호")
        second = PartyPasswordV3.hash_v3("password-with-unicode-암호")
        self.assertNotEqual(first, second)
        self.assertTrue(PartyPasswordV3.verify_v3("password-with-unicode-암호", first))
        self.assertFalse(PartyPasswordV3.verify_v3("incorrect", first))
        self.assertFalse(PartyPasswordV3.verify_v3("incorrect", "invalid-format"))

    def test_rate_limit_and_redis_outage_v3(self):
        redis_v3 = Mock()
        limiter = PartyRateLimiterV3(redis_v3)
        redis_v3.eval.return_value = [6, 37]
        with self.assertRaises(HTTPException) as result:
            limiter.consume_v3("user@example.test", "join:room", 5)
        self.assertEqual(result.exception.status_code, 429)
        self.assertEqual(result.exception.headers["Retry-After"], "37")
        self.assertNotIn("user@example.test", str(redis_v3.eval.call_args))
        redis_v3.eval.side_effect = RedisConnectionError("unavailable")
        with self.assertRaises(HTTPException) as result:
            limiter.consume_v3("user@example.test", "join:room", 5)
        self.assertEqual(result.exception.status_code, 503)

    @patch.dict("os.environ", {"GOOGLE_TOKEN_INFO_URL": "https://auth.example.test/tokeninfo"})
    @patch("api.live_map.party_v3.security.requests.get")
    def test_authentication_rejects_invalid_token_and_times_out_v3(self, get_v3):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="private-token")
        get_v3.return_value.status_code = 400
        with self.assertRaises(HTTPException) as result:
            authenticate_party_user_v3(credentials)
        self.assertEqual(result.exception.status_code, 401)
        get_v3.return_value.status_code = 200
        get_v3.return_value.json.return_value = {"email": "user@example.test", "verified_email": "false"}
        with self.assertRaises(HTTPException) as result:
            authenticate_party_user_v3(credentials)
        self.assertEqual(result.exception.status_code, 401)
        get_v3.return_value.json.return_value = {"email": "user@example.test", "verified_email": True}
        self.assertEqual(authenticate_party_user_v3(credentials), "user@example.test")
        get_v3.side_effect = requests.Timeout()
        with self.assertRaises(HTTPException) as result:
            authenticate_party_user_v3(credentials)
        self.assertEqual(result.exception.status_code, 503)
        self.assertEqual(get_v3.call_args.kwargs["timeout"], 5)


if __name__ == "__main__":
    unittest.main()
