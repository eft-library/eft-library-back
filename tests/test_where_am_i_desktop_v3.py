"""Desktop contract integration against isolated PostgreSQL and Redis only."""
import importlib.util
import json
import re
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import create_engine, text, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker

from api.where_am_i.metadata_v3 import DesktopReleaseV3, MapAliasV3
from api.where_am_i.analytics_v3 import RaidStateEventV3, VersionCheckEventV3, DesktopApiFailureV3
from api.where_am_i.where_am_i_router import router
from database import V3Database
from util.location_socket_v3 import latest_key_v3, websocket_handler_v3

HAS_SERVERS_V3 = all(importlib.util.find_spec(name) for name in ('pgserver', 'redislite'))


@unittest.skipUnless(HAS_SERVERS_V3, 'Install pgserver and redislite for isolated integration tests')
class DesktopContractTestV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pgserver
        import redislite
        cls.root_v3 = tempfile.TemporaryDirectory(prefix='desktop-contract-v3-')
        cls.addClassCleanup(cls.root_v3.cleanup)
        cls.server_v3 = pgserver.get_server(Path(cls.root_v3.name) / 'postgres', cleanup_mode='delete')
        cls.addClassCleanup(cls.server_v3.cleanup)
        cls.engine_v3 = create_engine(cls.server_v3.get_uri())
        cls.addClassCleanup(cls.engine_v3.dispose)
        cls.redis_server_v3 = redislite.Redis(cls.root_v3.name + '/redis.rdb', decode_responses=True)
        cls.addClassCleanup(cls.redis_server_v3._cleanup)
        cls.addClassCleanup(cls.redis_server_v3.close)
        root_v3 = Path(__file__).parents[1]
        source_v3 = (root_v3 / 'platform_db.sql').read_text()
        migration_v3 = (root_v3 / 'sql/migrations/20261019_where_am_i_desktop_metadata.sql').read_text()
        for table_v3 in ('where_am_i_releases', 'where_am_i_map_aliases'):
            definition_v3 = re.search(rf'create table if not exists {table_v3} \(.*?\n\);', source_v3, re.S).group()
            assert definition_v3 in migration_v3
        user_ddl_v3 = re.search(r'create table if not exists user_info\s*\(.*?\n\);', source_v3, re.S).group()
        with cls.engine_v3.connect() as conn_v3:
            conn_v3.exec_driver_sql(user_ddl_v3)
            conn_v3.exec_driver_sql(migration_v3)
            conn_v3.exec_driver_sql(migration_v3)
            analytics_ddl_v3 = (root_v3 / 'sql/migrations/20261019_where_am_i_analytics.sql').read_text()
            for table_v3 in ('where_am_i_raid_state_events', 'where_am_i_version_checks', 'where_am_i_api_failures'):
                assert re.search(rf'create table if not exists {table_v3} \(.*?\n\);', source_v3, re.S).group() in analytics_ddl_v3
            conn_v3.exec_driver_sql(analytics_ddl_v3)
            conn_v3.exec_driver_sql(analytics_ddl_v3)
            conn_v3.commit()
        cls.sessions_v3 = sessionmaker(cls.engine_v3)

    def setUp(self):
        self.redis_server_v3.flushdb()
        with self.engine_v3.begin() as conn_v3:
            conn_v3.execute(text('truncate where_am_i_releases, where_am_i_map_aliases, user_info, where_am_i_raid_state_events, where_am_i_version_checks, where_am_i_api_failures restart identity'))
            conn_v3.execute(text("insert into user_info(email) values ('owner@example.test'), ('other@example.test')"))
        patcher_v3 = patch.object(V3Database, 'SessionLocal', self.sessions_v3)
        patcher_v3.start()
        self.addCleanup(patcher_v3.stop)
        self.redis_v3 = Redis(unix_socket_path=self.redis_server_v3.socket_file, decode_responses=True)
        patcher_v3 = patch('util.location_socket_v3.get_location_redis_v3', return_value=self.redis_v3)
        patcher_v3.start()
        self.addCleanup(patcher_v3.stop)
        app_v3 = FastAPI()
        app_v3.include_router(router, prefix='/api/where-am-i')

        @app_v3.websocket('/ws')
        async def socket_endpoint_v3(socket_v3: WebSocket):
            await websocket_handler_v3(socket_v3, socket_v3.query_params.get('email', 'owner@example.test'))

        self.client_v3 = TestClient(app_v3)
        self.client_v3.__enter__()
        self.addCleanup(self.client_v3.__exit__, None, None, None)
        self.addCleanup(lambda: self.client_v3.portal.call(self.redis_v3.aclose))
        self.version_body_v3 = {'product':'where-am-i', 'current_version':'1.0.0.0',
                                'platform':'windows', 'architecture':'x64', 'channel':'stable'}
        now_v3 = datetime.now(timezone.utc)
        self.raid_v3 = {'email':'owner@example.test', 'map':'woods', 'is_active':True,
                        'started_at':(now_v3 - timedelta(seconds=5)).isoformat(), 'session_id':'a'*64,
                        'timer_observed_at':now_v3.isoformat(),
                        'raid_ends_at':(now_v3 + timedelta(minutes=35)).isoformat()}

    def post_v3(self, endpoint_v3, body_v3):
        return self.client_v3.post('/api/where-am-i/v3/' + endpoint_v3, json=body_v3)

    def release_v3(self, version_v3='1.10', **changes_v3):
        data_v3 = {'product':'where-am-i', 'version':version_v3, 'platform':'windows', 'architecture':'x64',
                   'channel':'stable', 'min_supported_version':'1.0', 'is_active':True,
                   'download_url':'https://eftlibrary.com/downloads/where-am-i', 'release_notes':'Plain text'}
        data_v3.update(changes_v3)
        with self.sessions_v3.begin() as session_v3:
            session_v3.add(DesktopReleaseV3(**data_v3))

    def until_v3(self, socket_v3, kind_v3):
        for _ in range(10):
            event_v3 = socket_v3.receive_json()
            if event_v3['type'] == kind_v3:
                return event_v3
        self.fail('Expected event not found')

    def test_version_numeric_optional_required_equal_and_future_client_v3(self):
        self.release_v3('1.9')
        self.release_v3('1.10', min_supported_version='1.5')
        for current_v3, available_v3, required_v3 in [('1.0',True,True), ('1.9',True,False),
                                                      ('1.10.0.0',False,False), ('2.0',False,False)]:
            response_v3 = self.post_v3('check-version', dict(self.version_body_v3, current_version=current_v3))
            self.assertEqual(response_v3.status_code, 200)
            data_v3 = response_v3.json()['data']
            self.assertEqual(data_v3['latest_version'], '1.10')
            self.assertEqual(data_v3['current_version'], current_v3)
            self.assertEqual(data_v3['update_available'], available_v3)
            self.assertEqual(data_v3['update_required'], required_v3)
        self.assertEqual(self.post_v3('check-version', dict(self.version_body_v3, architecture='arm64')).status_code, 422)
        for version_v3 in ('1', '1.0-beta', '1.0+abc', '1.0.0.0.0', '2147483648.0', '1. 0'):
            self.assertEqual(self.post_v3('check-version', dict(self.version_body_v3, current_version=version_v3)).status_code, 422)

    def test_release_visibility_and_failure_v3(self):
        self.release_v3('1.0', is_active=False)
        self.release_v3('2.0', published_at=datetime.now(timezone.utc)+timedelta(days=1))
        self.release_v3('3.0', architecture='arm64')
        self.assertEqual(self.post_v3('check-version', self.version_body_v3).status_code, 404)
        with patch.object(V3Database, 'SessionLocal', side_effect=OperationalError('offline', None, Exception())):
            self.assertEqual(self.post_v3('check-version', self.version_body_v3).status_code, 503)

    def test_release_url_and_minimum_validation_v3(self):
        for url_v3 in ('http://eftlibrary.com/a', 'https://github.com/a', 'https://eftlibrary.com:444/a',
                        'https://name@eftlibrary.com/a', 'https://eftlibrary.com.evil.test/a', None):
            with self.engine_v3.begin() as conn_v3:
                conn_v3.execute(text('truncate where_am_i_releases restart identity'))
            self.release_v3(download_url=url_v3)
            self.assertEqual(self.post_v3('check-version', self.version_body_v3).status_code, 503)
        with self.engine_v3.begin() as conn_v3:
            conn_v3.execute(text('truncate where_am_i_releases restart identity'))
        self.release_v3('1.0', download_url=None, min_supported_version='1.0.0.0')
        self.assertEqual(self.post_v3('check-version', self.version_body_v3).status_code, 200)
        with self.sessions_v3.begin() as session_v3:
            session_v3.query(DesktopReleaseV3).update({'min_supported_version':'2.0'})
        self.assertEqual(self.post_v3('check-version', self.version_body_v3).status_code, 503)

    def test_official_github_release_and_asset_urls_v3(self):
        urls_v3 = (
            'https://github.com/eft-library/eft-library-where-am-i/releases/tag/live-map-v2',
            'https://github.com/eft-library/eft-library-where-am-i/releases/download/live-map-v2/where-am-i.exe',
            'https://github.com/eft-library/eft-library-where-am-i/releases/latest',
        )
        self.release_v3(download_url=urls_v3[0])
        for url_v3 in urls_v3:
            with self.sessions_v3.begin() as session_v3:
                session_v3.query(DesktopReleaseV3).update({'download_url':url_v3})
            response_v3 = self.post_v3('check-version', self.version_body_v3)
            self.assertEqual(response_v3.status_code, 200)
            self.assertEqual(response_v3.json()['data']['download_url'], url_v3)
        for url_v3 in (
            'https://github.com/other/repository/releases/tag/v1',
            'https://github.com/eft-library/eft-library-where-am-i/issues',
            'https://github.com/eft-library/eft-library-where-am-i/releases/../../issues',
            'https://github.com/eft-library/eft-library-where-am-i/releases/%2e%2e/issues',
            'https://github.com.evil.test/eft-library/eft-library-where-am-i/releases/tag/v1',
        ):
            with self.sessions_v3.begin() as session_v3:
                session_v3.query(DesktopReleaseV3).update({'download_url':url_v3})
            self.assertEqual(self.post_v3('check-version', self.version_body_v3).status_code, 503)

    def test_alias_snapshot_normalization_version_change_and_constraints_v3(self):
        with self.sessions_v3.begin() as session_v3:
            session_v3.add_all([MapAliasV3(alias=' BIGMAP_preset ', map_slug='customs'),
                                MapAliasV3(alias='woods', map_slug='woods'),
                                MapAliasV3(alias='hidden', map_slug='woods', is_active=False)])
        first_v3 = self.client_v3.get('/api/where-am-i/v3/map-aliases').json()
        self.assertEqual(first_v3['status'], 200)
        self.assertEqual(first_v3['data']['aliases'], [{'alias':'bigmap','map':'customs'}, {'alias':'woods','map':'woods'}])
        self.assertEqual(first_v3, self.client_v3.get('/api/where-am-i/v3/map-aliases').json())
        with self.assertRaises(IntegrityError):
            with self.sessions_v3.begin() as session_v3:
                session_v3.add(MapAliasV3(alias='bigmap', map_slug='woods'))
        with self.sessions_v3.begin() as session_v3:
            session_v3.get(MapAliasV3, 'woods').is_active = False
        second_v3 = self.client_v3.get('/api/where-am-i/v3/map-aliases').json()['data']
        self.assertNotEqual(first_v3['data']['version'], second_v3['version'])
        self.assertEqual(len(second_v3['aliases']), 1)

    def test_slug_storage_is_unrestricted_and_old_check_is_removed_v3(self):
        migration_v3 = (Path(__file__).parents[1] / 'sql/migrations/20261019_where_am_i_desktop_metadata.sql').read_text()
        with self.engine_v3.connect() as conn_v3:
            conn_v3.exec_driver_sql("alter table where_am_i_map_aliases add constraint ck_where_am_i_alias_map check (map_slug in ('customs', 'woods'))")
            conn_v3.exec_driver_sql(migration_v3)
            conn_v3.commit()
        with self.sessions_v3.begin() as session_v3:
            session_v3.add(MapAliasV3(alias='future_alias', map_slug='future-map'))
        # The prepared client rejects unknown slugs for the entire snapshot, so the
        # API continues to fail closed until client support is expanded separately.
        response_v3 = self.client_v3.get('/api/where-am-i/v3/map-aliases')
        self.assertEqual(response_v3.status_code, 503)

    def test_alias_snapshot_limits_empty_and_database_failure_v3(self):
        endpoint_v3 = '/api/where-am-i/v3/map-aliases'
        self.assertEqual(self.client_v3.get(endpoint_v3).status_code, 404)
        with self.sessions_v3.begin() as session_v3:
            session_v3.add_all([MapAliasV3(alias=f'alias_{i}', map_slug='woods') for i in range(1024)])
        response_v3 = self.client_v3.get(endpoint_v3)
        self.assertEqual(response_v3.status_code, 200)
        self.assertLess(len(response_v3.content), 256*1024)
        with self.sessions_v3.begin() as session_v3:
            session_v3.add(MapAliasV3(alias='too_many', map_slug='woods'))
        self.assertEqual(self.client_v3.get(endpoint_v3).status_code, 503)
        with patch.object(V3Database, 'SessionLocal', side_effect=OperationalError('offline', None, Exception())):
            self.assertEqual(self.client_v3.get(endpoint_v3).status_code, 503)

    def test_timer_http_redis_and_personal_socket_preserve_payload_v3(self):
        with self.client_v3.websocket_connect('/ws') as socket_v3:
            self.until_v3(socket_v3, 'location_connection_status')
            response_v3 = self.post_v3('send-raid-state', self.raid_v3)
            self.assertEqual(response_v3.json(), {'status':200,'msg':'OK','data':True})
            event_v3 = self.until_v3(socket_v3, 'wpf_raid_state')
            self.assertNotIn('email', event_v3['payload'])
            self.assertEqual(event_v3['payload']['session_id'], 'a'*64)
            for key_v3 in ('timer_observed_at', 'raid_ends_at', 'started_at'):
                self.assertEqual(datetime.fromisoformat(event_v3['payload'][key_v3]), datetime.fromisoformat(self.raid_v3[key_v3]))
        key_v3 = latest_key_v3('owner@example.test') + ':raid'
        self.assertGreaterEqual(self.redis_server_v3.ttl(key_v3), 2158)
        cached_v3 = json.loads(self.redis_server_v3.get(key_v3))
        # Simulate a snapshot published >60 seconds ago while its timer remains valid.
        cached_v3['received_at_unix_us'] -= 61_000_000
        self.redis_server_v3.set(key_v3, json.dumps(cached_v3), ex=2100)
        with self.client_v3.websocket_connect('/ws') as socket_v3:
            replay_v3 = self.until_v3(socket_v3, 'wpf_raid_state')
            self.assertTrue(replay_v3['replayed'])
            self.assertEqual(replay_v3['payload']['raid_ends_at'], event_v3['payload']['raid_ends_at'])
        self.assertIsNone(self.redis_server_v3.get(latest_key_v3('other@example.test') + ':raid'))

    def test_legacy_missing_timer_null_and_supported_maps_v3(self):
        for map_v3 in ('woods', 'customs', 'shoreline'):
            self.assertEqual(self.post_v3('send-raid-state', {'email':'owner@example.test', 'map':map_v3, 'is_active':True}).status_code, 200)
        self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 200)
        cleared_v3 = dict(self.raid_v3, timer_observed_at=None, raid_ends_at=None)
        self.assertEqual(self.post_v3('send-raid-state', cleared_v3).status_code, 200)
        payload_v3 = json.loads(self.redis_server_v3.get(latest_key_v3('owner@example.test') + ':raid'))['payload']
        self.assertIsNone(payload_v3['raid_ends_at'])
        self.assertLessEqual(self.redis_server_v3.ttl(latest_key_v3('owner@example.test') + ':raid'), 60)

    def test_invalid_timer_context_times_session_and_user_failure_v3(self):
        changes_v3 = [{'timer_observed_at':None}, {'raid_ends_at':None}, {'timer_observed_at':'2026-10-19T00:00:00'},
                       {'started_at':'2026-10-19T00:00:00'}, {'raid_ends_at':self.raid_v3['timer_observed_at']},
                       {'session_id':'A'*64}, {'session_id':None}, {'started_at':None}, {'map':'unknown'},
                       {'map':None}, {'is_active':False}, {'timer_observed_at':123}]
        for change_v3 in changes_v3:
            with self.subTest(change_v3=change_v3):
                self.assertEqual(self.post_v3('send-raid-state', dict(self.raid_v3, **change_v3)).status_code, 422)
        self.assertEqual(self.post_v3('send-raid-state', dict(self.raid_v3, email='absent@example.test')).status_code, 404)
        with patch.object(V3Database, 'SessionLocal', side_effect=OperationalError('offline', None, Exception())):
            self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 503)
        with patch('api.where_am_i.service.send_wpf_raid_state', side_effect=RedisConnectionError()):
            self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 503)

    def test_expired_request_and_expired_cached_timer_are_not_activated_v3(self):
        now_v3 = datetime.now(timezone.utc)
        expired_v3 = dict(self.raid_v3, timer_observed_at=(now_v3-timedelta(minutes=2)).isoformat(),
                          raid_ends_at=(now_v3-timedelta(seconds=1)).isoformat())
        response_v3 = self.post_v3('send-raid-state', expired_v3)
        self.assertEqual((response_v3.status_code, response_v3.json()['detail']), (409,'RAID_TIMER_EXPIRED'))
        self.assertEqual(self.redis_server_v3.dbsize(), 0)
        self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 200)
        key_v3 = latest_key_v3('owner@example.test') + ':raid'
        cached_v3 = json.loads(self.redis_server_v3.get(key_v3))
        cached_v3['payload'].update({key_v3:expired_v3[key_v3] for key_v3 in ('timer_observed_at','raid_ends_at')})
        self.redis_server_v3.set(key_v3, json.dumps(cached_v3), ex=60)
        with self.client_v3.websocket_connect('/ws') as socket_v3:
            replay_v3 = self.until_v3(socket_v3, 'wpf_raid_state')
            self.assertIsNone(replay_v3['payload']['raid_ends_at'])
            self.assertIsNone(replay_v3['payload']['timer_observed_at'])

    def test_delayed_timer_session_changes_and_stale_request_v3(self):
        no_timer_v3 = dict(self.raid_v3, timer_observed_at=None, raid_ends_at=None)
        self.assertEqual(self.post_v3('send-raid-state', no_timer_v3).status_code, 200)
        self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 200)
        new_v3 = dict(self.raid_v3, session_id='b'*64,
                      started_at=(datetime.fromisoformat(self.raid_v3['started_at'])+timedelta(seconds=1)).isoformat())
        self.assertEqual(self.post_v3('send-raid-state', new_v3).status_code, 200)
        response_v3 = self.post_v3('send-raid-state', self.raid_v3)
        self.assertEqual((response_v3.status_code, response_v3.json()['detail']), (409,'RAID_STATE_STALE'))
        self.assertEqual(self.post_v3('send-raid-state', new_v3).status_code, 200)
        self.assertEqual(self.post_v3('send-raid-state', dict(new_v3, is_active=False, started_at=None,
                            timer_observed_at=None, raid_ends_at=None)).status_code, 200)
        cached_v3 = json.loads(self.redis_server_v3.get(latest_key_v3('owner@example.test') + ':raid'))
        self.assertIsNone(cached_v3['payload']['raid_ends_at'])

    def test_concurrent_states_keep_newest_known_start_v3(self):
        later_v3 = dict(self.raid_v3, session_id='b'*64,
                        started_at=(datetime.fromisoformat(self.raid_v3['started_at'])+timedelta(seconds=1)).isoformat())
        with ThreadPoolExecutor(max_workers=2) as workers_v3:
            statuses_v3 = list(workers_v3.map(
                lambda body_v3: self.post_v3('send-raid-state', body_v3).status_code,
                (self.raid_v3, later_v3)))
        self.assertEqual(statuses_v3[1], 200)
        self.assertIn(statuses_v3[0], (200, 409))
        cached_v3 = json.loads(self.redis_server_v3.get(latest_key_v3('owner@example.test') + ':raid'))
        self.assertEqual(cached_v3['payload']['session_id'], 'b'*64)

    def test_old_timer_observation_and_superseded_loading_session_v3(self):
        self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 200)
        older_v3 = dict(self.raid_v3, timer_observed_at=(datetime.fromisoformat(
            self.raid_v3['timer_observed_at'])-timedelta(seconds=1)).isoformat())
        self.assertEqual(self.post_v3('send-raid-state', older_v3).status_code, 409)
        loading_v3 = dict(self.raid_v3, session_id='b'*64, started_at=None, is_active=False,
                         timer_observed_at=None, raid_ends_at=None)
        self.assertEqual(self.post_v3('send-raid-state', loading_v3).status_code, 200)
        self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 409)
        cached_v3 = json.loads(self.redis_server_v3.get(latest_key_v3('owner@example.test') + ':raid'))
        self.assertEqual(cached_v3['payload']['session_id'], 'b'*64)
        self.assertIsNone(cached_v3['payload']['raid_ends_at'])

    def test_raid_analytics_event_id_retry_hash_and_rejected_state_v3(self):
        self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 200)
        self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 200)
        with self.sessions_v3() as session_v3:
            rows_v3 = list(session_v3.scalars(select(RaidStateEventV3).order_by(RaidStateEventV3.id)))
            self.assertEqual(len(rows_v3), 2)
            self.assertTrue(all(row_v3.is_success for row_v3 in rows_v3))
            self.assertEqual(rows_v3[0].state_hash, rows_v3[1].state_hash)
            self.assertEqual(rows_v3[0].user_key, rows_v3[1].user_key)
            self.assertNotEqual(rows_v3[0].event_id, rows_v3[1].event_id)
            self.assertEqual(rows_v3[0].session_id, 'a'*64)
            self.assertFalse(hasattr(rows_v3[0], 'email'))
            self.assertIsNotNone(rows_v3[0].received_at.tzinfo)
            cached_v3 = json.loads(self.redis_server_v3.get(latest_key_v3('owner@example.test') + ':raid'))
            self.assertEqual(str(rows_v3[1].event_id), cached_v3['event_id'])
        expired_v3 = dict(self.raid_v3, timer_observed_at=(datetime.now(timezone.utc)-timedelta(minutes=2)).isoformat(),
                          raid_ends_at=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat())
        self.assertEqual(self.post_v3('send-raid-state', expired_v3).status_code, 409)
        with self.sessions_v3() as session_v3:
            event_v3 = session_v3.scalars(select(RaidStateEventV3).order_by(RaidStateEventV3.id.desc())).first()
            failure_v3 = session_v3.scalars(select(DesktopApiFailureV3)).one()
            self.assertFalse(event_v3.is_success)
            self.assertIsNone(event_v3.event_id)
            self.assertEqual(failure_v3.result_code, 'RAID_TIMER_EXPIRED')
            self.assertEqual(failure_v3.user_key, event_v3.user_key)

    def test_version_analytics_success_and_not_found_v3(self):
        self.assertEqual(self.post_v3('check-version', self.version_body_v3).status_code, 404)
        self.release_v3()
        self.assertEqual(self.post_v3('check-version', self.version_body_v3).status_code, 200)
        with self.sessions_v3() as session_v3:
            rows_v3 = list(session_v3.scalars(select(VersionCheckEventV3).order_by(VersionCheckEventV3.id)))
            self.assertEqual(len(rows_v3), 2)
            self.assertFalse(rows_v3[0].is_success)
            self.assertIsNone(rows_v3[0].latest_version)
            self.assertEqual(rows_v3[1].latest_version, '1.10')
            self.assertTrue(rows_v3[1].update_available)
            self.assertTrue(rows_v3[1].is_success)
            self.assertFalse(hasattr(rows_v3[1], 'user_key'))
            failure_v3 = session_v3.scalars(select(DesktopApiFailureV3)).one()
            self.assertEqual(failure_v3.app_version, '1.0.0.0')

    def test_invalid_requests_only_log_safe_field_names_v3(self):
        self.assertEqual(self.post_v3('send-raid-state', dict(self.raid_v3, session_id='bad-private-value')).status_code, 422)
        self.assertEqual(self.post_v3('check-version', dict(self.version_body_v3, **{'private-secret-name':'private-secret-value'})).status_code, 422)
        response_v3 = self.client_v3.post('/api/where-am-i/v3/check-version', content='not-json', headers={'content-type':'application/json'})
        self.assertEqual(response_v3.status_code, 422)
        with self.sessions_v3() as session_v3:
            rows_v3 = list(session_v3.scalars(select(DesktopApiFailureV3)))
            self.assertEqual(len(rows_v3), 3)
            self.assertEqual(rows_v3[0].error_fields, ['body.session_id'])
            self.assertNotIn('private-secret', str([row_v3.error_fields for row_v3 in rows_v3]))
            self.assertEqual(list(session_v3.scalars(select(RaidStateEventV3))), [])
            self.assertEqual(list(session_v3.scalars(select(VersionCheckEventV3))), [])

    def test_analytics_failure_does_not_change_publication_or_http_result_v3(self):
        # Fail only the post-response transaction, not the operational DB check.
        with patch.object(self.sessions_v3, 'begin', side_effect=OperationalError('private-bound-value', None, Exception())):
            with self.assertLogs('api.where_am_i.analytics_v3', level='WARNING') as logs_v3:
                response_v3 = self.post_v3('send-raid-state', self.raid_v3)
        self.assertEqual(response_v3.json(), {'status':200,'msg':'OK','data':True})
        self.assertNotIn('private-bound-value', str(logs_v3.output))
        self.assertIsNotNone(self.redis_server_v3.get(latest_key_v3('owner@example.test') + ':raid'))
        self.release_v3()
        with patch.object(self.sessions_v3, 'begin', side_effect=OperationalError('offline', None, Exception())):
            self.assertEqual(self.post_v3('check-version', self.version_body_v3).status_code, 200)

    def test_requested_map_is_preserved_on_success_and_unknown_map_rejection_v3(self):
        self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 200)
        self.assertEqual(self.post_v3('send-raid-state', dict(self.raid_v3, map='NEW_Map_preset')).status_code, 422)
        with self.sessions_v3() as session_v3:
            state_v3 = session_v3.scalars(select(RaidStateEventV3)).one()
            self.assertEqual(state_v3.requested_map, 'woods')
            failure_v3 = session_v3.scalars(select(DesktopApiFailureV3)).one()
            self.assertEqual(failure_v3.requested_map, 'NEW_Map_preset')
            self.assertEqual(failure_v3.result_code, 'REQUEST_VALIDATION_ERROR')
        upgrade_v3 = (Path(__file__).parents[1] / 'sql/migrations/20261019_where_am_i_requested_map.sql').read_text()
        with self.engine_v3.connect() as conn_v3:
            conn_v3.exec_driver_sql(upgrade_v3)
            conn_v3.exec_driver_sql(upgrade_v3)
            conn_v3.commit()

    def test_recreate_map_analytics_preserves_version_history_v3(self):
        self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 200)
        self.assertEqual(self.post_v3('check-version', self.version_body_v3).status_code, 404)
        script_v3 = (Path(__file__).parents[1] / 'sql/migrations/20261019_recreate_where_am_i_map_analytics.sql').read_text()
        with self.engine_v3.connect() as conn_v3:
            conn_v3.exec_driver_sql(script_v3)
            conn_v3.exec_driver_sql(script_v3)
            conn_v3.commit()
        with self.sessions_v3() as session_v3:
            self.assertEqual(list(session_v3.scalars(select(RaidStateEventV3))), [])
            self.assertEqual(list(session_v3.scalars(select(DesktopApiFailureV3))), [])
            self.assertEqual(len(list(session_v3.scalars(select(VersionCheckEventV3)))), 1)
            columns_v3 = list(session_v3.scalars(text("select column_name from information_schema.columns where table_name='where_am_i_raid_state_events' order by ordinal_position")))
            self.assertEqual(columns_v3[columns_v3.index('map_slug')+1], 'requested_map')
        self.assertEqual(self.post_v3('send-raid-state', self.raid_v3).status_code, 200)
