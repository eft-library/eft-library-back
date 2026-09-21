"""Real local PostgreSQL/Redis tests. Optional dev dependencies: pgserver, redislite.

Servers use newly created temporary directories and Unix sockets. No environment
database/Redis URL is read for these tests, and the test servers are stopped afterward.
"""
import importlib.util
import re
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID

from redis.asyncio import Redis as AsyncRedisV3
from sqlalchemy import create_engine, delete, func, select, update
from sqlalchemy.exc import IntegrityError

from api.live_map.party_v3.models import PartyMarkerV3, PartyMemberV3, PartyRoomV3
from tests import test_live_map_party_realtime_v3 as realtime_tests_v3


HAS_SERVERS_V3 = all(importlib.util.find_spec(name) for name in ("pgserver", "redislite"))


@unittest.skipUnless(HAS_SERVERS_V3, "Install pgserver and redislite for local server integration tests")
class PartyPostgresTestV3(realtime_tests_v3.PartyRealtimeFixtureV3):
    @classmethod
    def setUpClass(cls):
        import pgserver
        import redislite

        cls.directory_server_v3 = tempfile.TemporaryDirectory(prefix="party-v3-integration-")
        cls.addClassCleanup(cls.directory_server_v3.cleanup)
        root = Path(cls.directory_server_v3.name)
        cls.postgres_server_v3 = pgserver.get_server(root / "postgres", cleanup_mode="delete")
        cls.addClassCleanup(cls.postgres_server_v3.cleanup)
        cls.redis_server_v3 = redislite.Redis(str(root / "redis.rdb"), decode_responses=True)
        cls.addClassCleanup(cls.redis_server_v3._cleanup)
        cls.addClassCleanup(cls.redis_server_v3.close)

        # Use authoritative checks, FKs and unique indexes. The bundled PostgreSQL
        # omits contrib/pg_trgm, so only its search-performance index is excluded.
        source = (Path(__file__).parents[1] / "platform_db.sql").read_text()
        statements = []
        for table in ("maps", "user_info", "live_map_floors"):
            definition = re.search(rf"create table if not exists {table}\s*\(.*?\n\);", source, re.S)
            assert definition is not None, table
            statements.append(definition.group())
        party_ddl = source[source.index("-- Live Map 파티 V3:"):]
        party_ddl = re.sub(
            r"create index if not exists idx_live_map_party_rooms_v3_name\s+.*?;", "", party_ddl, flags=re.S,
        )
        statements.append(party_ddl)
        engine = create_engine(cls.postgres_server_v3.get_uri())
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("\n".join(statements))
        finally:
            engine.dispose()

    def create_database_v3(self):
        self.engine_v3 = create_engine(self.postgres_server_v3.get_uri())
        with self.engine_v3.begin() as connection:
            connection.exec_driver_sql("""
                truncate live_map_party_rooms, user_info, live_map_floors, maps cascade
            """)

    def create_redis_v3(self):
        from redis import Redis

        self.redis_v3 = Redis(unix_socket_path=self.redis_server_v3.socket_file, decode_responses=True)
        self.redis_v3.flushdb()

    def create_subscriber_v3(self):
        return AsyncRedisV3(unix_socket_path=self.redis_server_v3.socket_file, decode_responses=True)

    def test_concurrent_joins_cannot_exceed_capacity_v3(self):
        room_id = self.create_v3(max_members=2)["room"]["id"]
        ready = threading.Barrier(2)

        def join_together_v3(user):
            ready.wait(timeout=5)
            return self.join_v3(room_id, user=user).status_code

        with ThreadPoolExecutor(max_workers=2) as workers:
            statuses = list(workers.map(join_together_v3, ("member", "other")))
        self.assertEqual(sorted(statuses), [200, 409])
        with self.sessions_v3() as session:
            members = list(session.scalars(select(PartyMemberV3).where(
                PartyMemberV3.room_id == UUID(room_id), PartyMemberV3.status == "joined",
            )))
            self.assertEqual(len(members), 2)
            self.assertEqual(len({member.color for member in members}), 2)

    def test_concurrent_marker_edits_detect_stale_version_v3(self):
        room_id = self.create_v3()["room"]["id"]
        marker_id = self.marker_v3(room_id).json()["data"]["id"]
        ready = threading.Barrier(2)

        def update_together_v3(x):
            ready.wait(timeout=5)
            return self.request_v3("PUT", f"/{room_id}/markers/{marker_id}", json={
                "floor_id": "floor-a", "x": x, "z": 2, "version": 1,
            }).status_code

        with ThreadPoolExecutor(max_workers=2) as workers:
            statuses = list(workers.map(update_together_v3, (3, 4)))
        self.assertEqual(sorted(statuses), [200, 409])
        with self.sessions_v3() as session:
            self.assertEqual(session.get(PartyMarkerV3, UUID(marker_id)).version, 2)

    def test_authoritative_constraints_and_room_delete_cascade_v3(self):
        room_id = self.create_v3()["room"]["id"]
        marker_id = self.marker_v3(room_id).json()["data"]["id"]
        with self.assertRaises(IntegrityError):
            with self.sessions_v3.begin() as session:
                session.execute(update(PartyMarkerV3).where(PartyMarkerV3.id == UUID(marker_id)).values(x=float("nan")))
        with self.sessions_v3.begin() as session:
            session.execute(delete(PartyRoomV3).where(PartyRoomV3.id == UUID(room_id)))
        with self.sessions_v3() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(PartyMemberV3)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(PartyMarkerV3)), 0)

    # Exercise identical client contracts against real servers rather than duplicate test bodies.
    test_real_redis_socket_delivery_v3 = realtime_tests_v3.PartyRealtimeTestV3.test_two_clients_receive_ping_and_persisted_marker_changes_v3
    test_real_redis_kick_and_close_v3 = realtime_tests_v3.PartyRealtimeTestV3.test_kick_and_room_close_disconnect_sockets_v3
    test_real_postgres_cleanup_transfer_v3 = realtime_tests_v3.PartyRealtimeTestV3.test_multiple_tabs_count_once_and_cleanup_transfers_owner_v3


if __name__ == "__main__":
    unittest.main()
