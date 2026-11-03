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

from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import create_engine, delete, func, select, update
from sqlalchemy.exc import IntegrityError

from api.live_map.party.models import PartyMarker, PartyMember, PartyRoom
from tests import test_live_map_party_realtime as realtime_tests


HAS_SERVERS = all(importlib.util.find_spec(name) for name in ("pgserver", "redislite"))


@unittest.skipUnless(HAS_SERVERS, "Install pgserver and redislite for local server integration tests")
class PartyPostgresTest(realtime_tests.PartyRealtimeFixture):
    @classmethod
    def setUpClass(cls):
        import pgserver
        import redislite

        cls.directory_server = tempfile.TemporaryDirectory(prefix="party-v3-integration-")
        cls.addClassCleanup(cls.directory_server.cleanup)
        root = Path(cls.directory_server.name)
        cls.postgres_server = pgserver.get_server(root / "postgres", cleanup_mode="delete")
        cls.addClassCleanup(cls.postgres_server.cleanup)
        cls.redis_server = redislite.Redis(str(root / "redis.rdb"), decode_responses=True)
        cls.addClassCleanup(cls.redis_server._cleanup)
        cls.addClassCleanup(cls.redis_server.close)

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
        engine = create_engine(cls.postgres_server.get_uri())
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("\n".join(statements))
        finally:
            engine.dispose()

    def create_database(self):
        self.engine = create_engine(self.postgres_server.get_uri())
        with self.engine.begin() as connection:
            connection.exec_driver_sql("""
                truncate live_map_party_rooms, user_info, live_map_floors, maps cascade
            """)

    def create_redis(self):
        from redis import Redis

        self.redis = Redis(unix_socket_path=self.redis_server.socket_file, decode_responses=True)
        self.redis.flushdb()

    def create_subscriber(self):
        return AsyncRedis(unix_socket_path=self.redis_server.socket_file, decode_responses=True)

    def test_concurrent_joins_cannot_exceed_capacity(self):
        room_id = self.create(max_members=2)["room"]["id"]
        ready = threading.Barrier(2)

        def join_together(user):
            ready.wait(timeout=5)
            return self.join(room_id, user=user).status_code

        with ThreadPoolExecutor(max_workers=2) as workers:
            statuses = list(workers.map(join_together, ("member", "other")))
        self.assertEqual(sorted(statuses), [200, 409])
        with self.sessions() as session:
            members = list(session.scalars(select(PartyMember).where(
                PartyMember.room_id == UUID(room_id), PartyMember.status == "joined",
            )))
            self.assertEqual(len(members), 2)
            self.assertEqual(len({member.color for member in members}), 2)

    def test_marker_map_migration_backfills_existing_rows(self):
        room_id = self.create()["room"]["id"]
        self.marker(room_id, floor_id="floor-child")
        with self.engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE live_map_party_markers DROP COLUMN map_id")
        migration = (Path(__file__).parents[1] / "sql/migrations/20260922_party_marker_map_v3.sql").read_text()
        with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(migration)
            connection.exec_driver_sql(migration)
            self.assertEqual(connection.exec_driver_sql("SELECT map_id FROM live_map_party_markers").scalar_one(), "map-a")

    def test_concurrent_marker_edits_detect_stale_version(self):
        room_id = self.create()["room"]["id"]
        marker_id = self.marker(room_id).json()["data"]["id"]
        ready = threading.Barrier(2)

        def update_together(x):
            ready.wait(timeout=5)
            return self.request("PUT", f"/{room_id}/markers/{marker_id}", json={
                "floor_id": "floor-a", "x": x, "z": 2, "version": 1,
            }).status_code

        with ThreadPoolExecutor(max_workers=2) as workers:
            statuses = list(workers.map(update_together, (3, 4)))
        self.assertEqual(sorted(statuses), [200, 409])
        with self.sessions() as session:
            self.assertEqual(session.get(PartyMarker, UUID(marker_id)).version, 2)

    def test_authoritative_constraints_and_room_delete_cascade(self):
        room_id = self.create()["room"]["id"]
        marker_id = self.marker(room_id).json()["data"]["id"]
        with self.assertRaises(IntegrityError):
            with self.sessions.begin() as session:
                session.execute(update(PartyMarker).where(PartyMarker.id == UUID(marker_id)).values(x=float("nan")))
        with self.sessions.begin() as session:
            session.execute(delete(PartyRoom).where(PartyRoom.id == UUID(room_id)))
        with self.sessions() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(PartyMember)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(PartyMarker)), 0)

    # Exercise identical client contracts against real servers rather than duplicate test bodies.
    test_real_redis_socket_delivery = realtime_tests.PartyRealtimeTest.test_two_clients_receive_ping_and_persisted_marker_changes
    test_real_redis_kick_and_close = realtime_tests.PartyRealtimeTest.test_kick_and_room_close_disconnect_sockets
    test_real_postgres_cleanup_transfer = realtime_tests.PartyRealtimeTest.test_multiple_tabs_count_once_and_cleanup_transfers_owner


if __name__ == "__main__":
    unittest.main()
