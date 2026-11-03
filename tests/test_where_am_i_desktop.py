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

from api.where_am_i.metadata import DesktopRelease, MapAlias
from api.where_am_i.analytics import RaidStateEvent, VersionCheckEvent, DesktopApiFailure
from api.where_am_i.where_am_i_router import router
from database import Database
from util.location_socket import latest_key, websocket_handler

HAS_SERVERS = all(importlib.util.find_spec(name) for name in ('pgserver', 'redislite'))


@unittest.skipUnless(HAS_SERVERS, 'Install pgserver and redislite for isolated integration tests')
class DesktopContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pgserver
        import redislite
        cls.root = tempfile.TemporaryDirectory(prefix='desktop-contract-v3-')
        cls.addClassCleanup(cls.root.cleanup)
        cls.server = pgserver.get_server(Path(cls.root.name) / 'postgres', cleanup_mode='delete')
        cls.addClassCleanup(cls.server.cleanup)
        cls.engine = create_engine(cls.server.get_uri())
        cls.addClassCleanup(cls.engine.dispose)
        cls.redis_server = redislite.Redis(cls.root.name + '/redis.rdb', decode_responses=True)
        cls.addClassCleanup(cls.redis_server._cleanup)
        cls.addClassCleanup(cls.redis_server.close)
        root = Path(__file__).parents[1]
        source = (root / 'platform_db.sql').read_text()
        migration = (root / 'sql/migrations/20261019_where_am_i_desktop_metadata.sql').read_text()
        for table in ('where_am_i_releases', 'where_am_i_map_aliases'):
            definition = re.search(rf'create table if not exists {table} \(.*?\n\);', source, re.S).group()
            assert definition in migration
        user_ddl = re.search(r'create table if not exists user_info\s*\(.*?\n\);', source, re.S).group()
        with cls.engine.connect() as conn:
            conn.exec_driver_sql(user_ddl)
            conn.exec_driver_sql(migration)
            conn.exec_driver_sql(migration)
            analytics_ddl = (root / 'sql/migrations/20261019_where_am_i_analytics.sql').read_text()
            for table in ('where_am_i_raid_state_events', 'where_am_i_version_checks', 'where_am_i_api_failures'):
                assert re.search(rf'create table if not exists {table} \(.*?\n\);', source, re.S).group() in analytics_ddl
            conn.exec_driver_sql(analytics_ddl)
            conn.exec_driver_sql(analytics_ddl)
            conn.commit()
        cls.sessions = sessionmaker(cls.engine)

    def setUp(self):
        self.redis_server.flushdb()
        with self.engine.begin() as conn:
            conn.execute(text('truncate where_am_i_releases, where_am_i_map_aliases, user_info, where_am_i_raid_state_events, where_am_i_version_checks, where_am_i_api_failures restart identity'))
            conn.execute(text("insert into where_am_i_map_aliases(alias, map_slug) values ('woods', 'woods')"))
            conn.execute(text("insert into user_info(email) values ('owner@example.test'), ('other@example.test')"))
        patcher = patch.object(Database, 'SessionLocal', self.sessions)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.redis = Redis(unix_socket_path=self.redis_server.socket_file, decode_responses=True)
        patcher = patch('util.location_socket.get_location_redis', return_value=self.redis)
        patcher.start()
        self.addCleanup(patcher.stop)
        app = FastAPI()
        app.include_router(router, prefix='/api/where-am-i')

        @app.websocket('/ws')
        async def socket_endpoint(socket: WebSocket):
            await websocket_handler(socket, socket.query_params.get('email', 'owner@example.test'))

        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.addCleanup(lambda: self.client.portal.call(self.redis.aclose))
        self.version_body = {'product':'where-am-i', 'current_version':'1.0.0.0',
                                'platform':'windows', 'architecture':'x64', 'channel':'stable'}
        utc_now = datetime.now(timezone.utc)
        self.raid = {'email':'owner@example.test', 'map':'woods', 'is_active':True,
                        'started_at':(utc_now - timedelta(seconds=5)).isoformat(), 'session_id':'a'*64,
                        'timer_observed_at':utc_now.isoformat(),
                        'raid_ends_at':(utc_now + timedelta(minutes=35)).isoformat()}

    def post(self, endpoint, body):
        return self.client.post('/api/where-am-i/v3/' + endpoint, json=body)

    def release(self, version='1.10', **changes):
        data = {'product':'where-am-i', 'version':version, 'platform':'windows', 'architecture':'x64',
                   'channel':'stable', 'min_supported_version':'1.0', 'is_active':True,
                   'download_url':'https://eftlibrary.com/downloads/where-am-i', 'release_notes':'Plain text'}
        data.update(changes)
        with self.sessions.begin() as session:
            session.add(DesktopRelease(**data))

    def until(self, socket, kind):
        for _ in range(10):
            build_event = socket.receive_json()
            if build_event['type'] == kind:
                return build_event
        self.fail('Expected event not found')

    def test_version_numeric_optional_required_equal_and_future_client(self):
        self.release('1.9')
        self.release('1.10', min_supported_version='1.5')
        for current, available, required in [('1.0',True,True), ('1.9',True,False),
                                                      ('1.10.0.0',False,False), ('2.0',False,False)]:
            api_response = self.post('check-version', dict(self.version_body, current_version=current))
            self.assertEqual(api_response.status_code, 200)
            data = api_response.json()['data']
            self.assertEqual(data['latest_version'], '1.10')
            self.assertEqual(data['current_version'], current)
            self.assertEqual(data['update_available'], available)
            self.assertEqual(data['update_required'], required)
        self.assertEqual(self.post('check-version', dict(self.version_body, architecture='arm64')).status_code, 422)
        for version in ('1', '1.0-beta', '1.0+abc', '1.0.0.0.0', '2147483648.0', '1. 0'):
            self.assertEqual(self.post('check-version', dict(self.version_body, current_version=version)).status_code, 422)

    def test_release_visibility_and_failure(self):
        self.release('1.0', is_active=False)
        self.release('2.0', published_at=datetime.now(timezone.utc)+timedelta(days=1))
        self.release('3.0', architecture='arm64')
        self.assertEqual(self.post('check-version', self.version_body).status_code, 404)
        with patch.object(Database, 'SessionLocal', side_effect=OperationalError('offline', None, Exception())):
            self.assertEqual(self.post('check-version', self.version_body).status_code, 503)

    def test_release_url_and_minimum_validation(self):
        for url in ('http://eftlibrary.com/a', 'https://github.com/a', 'https://eftlibrary.com:444/a',
                        'https://name@eftlibrary.com/a', 'https://eftlibrary.com.evil.test/a', None):
            with self.engine.begin() as conn:
                conn.execute(text('truncate where_am_i_releases restart identity'))
            self.release(download_url=url)
            self.assertEqual(self.post('check-version', self.version_body).status_code, 503)
        with self.engine.begin() as conn:
            conn.execute(text('truncate where_am_i_releases restart identity'))
        self.release('1.0', download_url=None, min_supported_version='1.0.0.0')
        self.assertEqual(self.post('check-version', self.version_body).status_code, 200)
        with self.sessions.begin() as session:
            session.query(DesktopRelease).update({'min_supported_version':'2.0'})
        self.assertEqual(self.post('check-version', self.version_body).status_code, 503)

    def test_official_github_release_and_asset_urls(self):
        urls = (
            'https://github.com/eft-library/eft-library-where-am-i/releases/tag/live-map-v2',
            'https://github.com/eft-library/eft-library-where-am-i/releases/download/live-map-v2/where-am-i.exe',
            'https://github.com/eft-library/eft-library-where-am-i/releases/latest',
        )
        self.release(download_url=urls[0])
        for url in urls:
            with self.sessions.begin() as session:
                session.query(DesktopRelease).update({'download_url':url})
            api_response = self.post('check-version', self.version_body)
            self.assertEqual(api_response.status_code, 200)
            self.assertEqual(api_response.json()['data']['download_url'], url)
        for url in (
            'https://github.com/other/repository/releases/tag/v1',
            'https://github.com/eft-library/eft-library-where-am-i/issues',
            'https://github.com/eft-library/eft-library-where-am-i/releases/../../issues',
            'https://github.com/eft-library/eft-library-where-am-i/releases/%2e%2e/issues',
            'https://github.com.evil.test/eft-library/eft-library-where-am-i/releases/tag/v1',
        ):
            with self.sessions.begin() as session:
                session.query(DesktopRelease).update({'download_url':url})
            self.assertEqual(self.post('check-version', self.version_body).status_code, 503)

    def test_alias_snapshot_normalization_version_change_and_constraints(self):
        with self.sessions.begin() as session:
            session.add_all([MapAlias(alias=' BIGMAP_preset ', map_slug='customs'),
                                MapAlias(alias='hidden', map_slug='woods', is_active=False)])
        first = self.client.get('/api/where-am-i/v3/map-aliases').json()
        self.assertEqual(first['status'], 200)
        self.assertEqual(first['data']['aliases'], [{'alias':'bigmap','map':'customs'}, {'alias':'woods','map':'woods'}])
        self.assertEqual(first, self.client.get('/api/where-am-i/v3/map-aliases').json())
        with self.assertRaises(IntegrityError):
            with self.sessions.begin() as session:
                session.add(MapAlias(alias='bigmap', map_slug='woods'))
        with self.sessions.begin() as session:
            session.get(MapAlias, 'woods').is_active = False
        second = self.client.get('/api/where-am-i/v3/map-aliases').json()['data']
        self.assertNotEqual(first['data']['version'], second['version'])
        self.assertEqual(len(second['aliases']), 1)

    def test_slug_storage_is_unrestricted_and_old_check_is_removed(self):
        migration = (Path(__file__).parents[1] / 'sql/migrations/20261019_where_am_i_desktop_metadata.sql').read_text()
        with self.engine.connect() as conn:
            conn.exec_driver_sql("alter table where_am_i_map_aliases add constraint ck_where_am_i_alias_map check (map_slug in ('customs', 'woods'))")
            conn.exec_driver_sql(migration)
            conn.commit()
        with self.sessions.begin() as session:
            session.add(MapAlias(alias='future_alias', map_slug='future-map'))
        api_response = self.client.get('/api/where-am-i/v3/map-aliases')
        self.assertEqual(api_response.status_code, 200)
        self.assertIn({'alias':'future_alias', 'map':'future-map'}, api_response.json()['data']['aliases'])

    def test_alias_snapshot_limits_empty_and_database_failure(self):
        with self.engine.begin() as conn:
            conn.execute(text('delete from where_am_i_map_aliases'))
        endpoint = '/api/where-am-i/v3/map-aliases'
        self.assertEqual(self.client.get(endpoint).status_code, 404)
        with self.sessions.begin() as session:
            session.add_all([MapAlias(alias=f'alias_{i}', map_slug='woods') for i in range(1024)])
        api_response = self.client.get(endpoint)
        self.assertEqual(api_response.status_code, 200)
        self.assertLess(len(api_response.content), 256*1024)
        with self.sessions.begin() as session:
            session.add(MapAlias(alias='too_many', map_slug='woods'))
        self.assertEqual(self.client.get(endpoint).status_code, 503)
        with patch.object(Database, 'SessionLocal', side_effect=OperationalError('offline', None, Exception())):
            self.assertEqual(self.client.get(endpoint).status_code, 503)

    def test_timer_http_redis_and_personal_socket_preserve_payload(self):
        with self.client.websocket_connect('/ws') as socket:
            self.until(socket, 'location_connection_status')
            api_response = self.post('send-raid-state', self.raid)
            self.assertEqual(api_response.json(), {'status':200,'msg':'OK','data':True})
            build_event = self.until(socket, 'wpf_raid_state')
            self.assertNotIn('email', build_event['payload'])
            self.assertEqual(build_event['payload']['session_id'], 'a'*64)
            for key in ('timer_observed_at', 'raid_ends_at', 'started_at'):
                self.assertEqual(datetime.fromisoformat(build_event['payload'][key]), datetime.fromisoformat(self.raid[key]))
        key = latest_key('owner@example.test') + ':raid'
        self.assertGreaterEqual(self.redis_server.ttl(key), 2158)
        cached = json.loads(self.redis_server.get(key))
        # Simulate a snapshot published >60 seconds ago while its timer remains valid.
        cached['received_at_unix_us'] -= 61_000_000
        self.redis_server.set(key, json.dumps(cached), ex=2100)
        with self.client.websocket_connect('/ws') as socket:
            replay = self.until(socket, 'wpf_raid_state')
            self.assertTrue(replay['replayed'])
            self.assertEqual(replay['payload']['raid_ends_at'], build_event['payload']['raid_ends_at'])
        self.assertIsNone(self.redis_server.get(latest_key('other@example.test') + ':raid'))

    def test_legacy_missing_timer_null_and_supported_maps(self):
        for map in ('woods', 'customs', 'shoreline'):
            self.assertEqual(self.post('send-raid-state', {'email':'owner@example.test', 'map':map, 'is_active':True}).status_code, 200)
        self.assertEqual(self.post('send-raid-state', self.raid).status_code, 200)
        cleared = dict(self.raid, timer_observed_at=None, raid_ends_at=None)
        self.assertEqual(self.post('send-raid-state', cleared).status_code, 200)
        payload = json.loads(self.redis_server.get(latest_key('owner@example.test') + ':raid'))['payload']
        self.assertIsNone(payload['raid_ends_at'])
        self.assertLessEqual(self.redis_server.ttl(latest_key('owner@example.test') + ':raid'), 60)

    def test_invalid_timer_context_times_session_and_user_failure(self):
        changes = [{'timer_observed_at':None}, {'raid_ends_at':None}, {'timer_observed_at':'2026-10-19T00:00:00'},
                       {'started_at':'2026-10-19T00:00:00'}, {'raid_ends_at':self.raid['timer_observed_at']},
                       {'session_id':'A'*64}, {'session_id':None}, {'started_at':None}, {'map':'unknown'},
                       {'map':None}, {'is_active':False}, {'timer_observed_at':123}]
        for change in changes:
            with self.subTest(change=change):
                self.assertEqual(self.post('send-raid-state', dict(self.raid, **change)).status_code, 422)
        self.assertEqual(self.post('send-raid-state', dict(self.raid, email='absent@example.test')).status_code, 404)
        with patch.object(Database, 'SessionLocal', side_effect=OperationalError('offline', None, Exception())):
            self.assertEqual(self.post('send-raid-state', self.raid).status_code, 503)
        with patch('api.where_am_i.service.send_wpf_raid_state', side_effect=RedisConnectionError()):
            self.assertEqual(self.post('send-raid-state', self.raid).status_code, 503)

    def test_expired_request_and_expired_cached_timer_are_not_activated(self):
        utc_now = datetime.now(timezone.utc)
        expired = dict(self.raid, timer_observed_at=(utc_now-timedelta(minutes=2)).isoformat(),
                          raid_ends_at=(utc_now-timedelta(seconds=1)).isoformat())
        api_response = self.post('send-raid-state', expired)
        self.assertEqual((api_response.status_code, api_response.json()['detail']), (409,'RAID_TIMER_EXPIRED'))
        self.assertEqual(self.redis_server.dbsize(), 0)
        self.assertEqual(self.post('send-raid-state', self.raid).status_code, 200)
        key = latest_key('owner@example.test') + ':raid'
        cached = json.loads(self.redis_server.get(key))
        cached['payload'].update({key:expired[key] for key in ('timer_observed_at','raid_ends_at')})
        self.redis_server.set(key, json.dumps(cached), ex=60)
        with self.client.websocket_connect('/ws') as socket:
            replay = self.until(socket, 'wpf_raid_state')
            self.assertIsNone(replay['payload']['raid_ends_at'])
            self.assertIsNone(replay['payload']['timer_observed_at'])

    def test_delayed_timer_session_changes_and_stale_request(self):
        no_timer = dict(self.raid, timer_observed_at=None, raid_ends_at=None)
        self.assertEqual(self.post('send-raid-state', no_timer).status_code, 200)
        self.assertEqual(self.post('send-raid-state', self.raid).status_code, 200)
        new = dict(self.raid, session_id='b'*64,
                      started_at=(datetime.fromisoformat(self.raid['started_at'])+timedelta(seconds=1)).isoformat())
        self.assertEqual(self.post('send-raid-state', new).status_code, 200)
        api_response = self.post('send-raid-state', self.raid)
        self.assertEqual((api_response.status_code, api_response.json()['detail']), (409,'RAID_STATE_STALE'))
        self.assertEqual(self.post('send-raid-state', new).status_code, 200)
        self.assertEqual(self.post('send-raid-state', dict(new, is_active=False, started_at=None,
                            timer_observed_at=None, raid_ends_at=None)).status_code, 200)
        cached = json.loads(self.redis_server.get(latest_key('owner@example.test') + ':raid'))
        self.assertIsNone(cached['payload']['raid_ends_at'])

    def test_concurrent_states_keep_newest_known_start(self):
        later = dict(self.raid, session_id='b'*64,
                        started_at=(datetime.fromisoformat(self.raid['started_at'])+timedelta(seconds=1)).isoformat())
        with ThreadPoolExecutor(max_workers=2) as workers:
            statuses = list(workers.map(
                lambda body: self.post('send-raid-state', body).status_code,
                (self.raid, later)))
        self.assertEqual(statuses[1], 200)
        self.assertIn(statuses[0], (200, 409))
        cached = json.loads(self.redis_server.get(latest_key('owner@example.test') + ':raid'))
        self.assertEqual(cached['payload']['session_id'], 'b'*64)

    def test_old_timer_observation_and_superseded_loading_session(self):
        self.assertEqual(self.post('send-raid-state', self.raid).status_code, 200)
        older = dict(self.raid, timer_observed_at=(datetime.fromisoformat(
            self.raid['timer_observed_at'])-timedelta(seconds=1)).isoformat())
        self.assertEqual(self.post('send-raid-state', older).status_code, 409)
        loading = dict(self.raid, session_id='b'*64, started_at=None, is_active=False,
                         timer_observed_at=None, raid_ends_at=None)
        self.assertEqual(self.post('send-raid-state', loading).status_code, 200)
        self.assertEqual(self.post('send-raid-state', self.raid).status_code, 409)
        cached = json.loads(self.redis_server.get(latest_key('owner@example.test') + ':raid'))
        self.assertEqual(cached['payload']['session_id'], 'b'*64)
        self.assertIsNone(cached['payload']['raid_ends_at'])

    def test_empty_inactive_state_is_published_without_raid_analytics(self):
        body = {'email': 'owner@example.test', 'map': None, 'is_active': False,
                   'started_at': None, 'timer_observed_at': None, 'raid_ends_at': None}
        self.assertEqual(self.post('send-raid-state', body).status_code, 200)
        cached = json.loads(self.redis_server.get(latest_key('owner@example.test') + ':raid'))
        self.assertFalse(cached['payload']['is_active'])
        self.assertIsNone(cached['payload']['map'])
        with self.sessions() as session:
            self.assertEqual(list(session.scalars(select(RaidStateEvent))), [])
        # A map-bearing loading state remains useful for analysis.
        self.assertEqual(self.post('send-raid-state', dict(body, map='woods')).status_code, 200)
        with self.sessions() as session:
            self.assertEqual(session.scalars(select(RaidStateEvent)).one().requested_map, 'woods')

    def test_raid_analytics_event_id_retry_hash_and_rejected_state(self):
        self.assertEqual(self.post('send-raid-state', self.raid).status_code, 200)
        self.assertEqual(self.post('send-raid-state', self.raid).status_code, 200)
        with self.sessions() as session:
            rows = list(session.scalars(select(RaidStateEvent).order_by(RaidStateEvent.id)))
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row.is_success for row in rows))
            self.assertEqual(rows[0].state_hash, rows[1].state_hash)
            self.assertEqual(rows[0].user_key, rows[1].user_key)
            self.assertNotEqual(rows[0].event_id, rows[1].event_id)
            self.assertEqual(rows[0].session_id, 'a'*64)
            self.assertEqual(rows[0].email, 'owner@example.test')
            self.assertIsNotNone(rows[0].received_at.tzinfo)
            cached = json.loads(self.redis_server.get(latest_key('owner@example.test') + ':raid'))
            self.assertEqual(str(rows[1].event_id), cached['event_id'])
        expired = dict(self.raid, timer_observed_at=(datetime.now(timezone.utc)-timedelta(minutes=2)).isoformat(),
                          raid_ends_at=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat())
        self.assertEqual(self.post('send-raid-state', expired).status_code, 409)
        with self.sessions() as session:
            build_event = session.scalars(select(RaidStateEvent).order_by(RaidStateEvent.id.desc())).first()
            failure = session.scalars(select(DesktopApiFailure)).one()
            self.assertFalse(build_event.is_success)
            self.assertIsNone(build_event.event_id)
            self.assertEqual(failure.result_code, 'RAID_TIMER_EXPIRED')
            self.assertEqual(failure.user_key, build_event.user_key)

    def test_version_analytics_success_and_not_found(self):
        self.assertEqual(self.post('check-version', self.version_body).status_code, 404)
        self.release()
        self.assertEqual(self.post('check-version', self.version_body).status_code, 200)
        with self.sessions() as session:
            rows = list(session.scalars(select(VersionCheckEvent).order_by(VersionCheckEvent.id)))
            self.assertEqual(len(rows), 2)
            self.assertFalse(rows[0].is_success)
            self.assertIsNone(rows[0].latest_version)
            self.assertEqual(rows[1].latest_version, '1.10')
            self.assertTrue(rows[1].update_available)
            self.assertTrue(rows[1].is_success)
            self.assertFalse(hasattr(rows[1], 'user_key'))
            failure = session.scalars(select(DesktopApiFailure)).one()
            self.assertEqual(failure.app_version, '1.0.0.0')

    def test_invalid_requests_only_log_safe_field_names(self):
        self.assertEqual(self.post('send-raid-state', dict(self.raid, session_id='bad-private-value')).status_code, 422)
        self.assertEqual(self.post('check-version', dict(self.version_body, **{'private-secret-name':'private-secret-value'})).status_code, 422)
        api_response = self.client.post('/api/where-am-i/v3/check-version', content='not-json', headers={'content-type':'application/json'})
        self.assertEqual(api_response.status_code, 422)
        with self.sessions() as session:
            rows = list(session.scalars(select(DesktopApiFailure)))
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0].error_fields, ['body.session_id'])
            self.assertNotIn('private-secret', str([row.error_fields for row in rows]))
            self.assertEqual(list(session.scalars(select(RaidStateEvent))), [])
            self.assertEqual(list(session.scalars(select(VersionCheckEvent))), [])

    def test_analytics_failure_does_not_change_publication_or_http_result(self):
        # Fail only the post-response transaction, not the operational DB check.
        with patch.object(self.sessions, 'begin', side_effect=OperationalError('private-bound-value', None, Exception())):
            with self.assertLogs('api.where_am_i.analytics', level='WARNING') as logs:
                api_response = self.post('send-raid-state', self.raid)
        self.assertEqual(api_response.json(), {'status':200,'msg':'OK','data':True})
        self.assertNotIn('private-bound-value', str(logs.output))
        self.assertIsNotNone(self.redis_server.get(latest_key('owner@example.test') + ':raid'))
        self.release()
        with patch.object(self.sessions, 'begin', side_effect=OperationalError('offline', None, Exception())):
            self.assertEqual(self.post('check-version', self.version_body).status_code, 200)

    def test_requested_map_is_preserved_on_success_and_unknown_map_rejection(self):
        self.assertEqual(self.post('send-raid-state', self.raid).status_code, 200)
        self.assertEqual(self.post('send-raid-state', dict(self.raid, map='NEW_Map_preset')).status_code, 422)
        with self.sessions() as session:
            connection_state = session.scalars(select(RaidStateEvent)).one()
            self.assertEqual(connection_state.requested_map, 'woods')
            failure = session.scalars(select(DesktopApiFailure)).one()
            self.assertEqual(failure.requested_map, 'NEW_Map_preset')
            self.assertEqual(failure.result_code, 'RAID_MAP_UNRESOLVED')
        upgrade = (Path(__file__).parents[1] / 'sql/migrations/20261019_where_am_i_requested_map.sql').read_text()
        with self.engine.connect() as conn:
            conn.exec_driver_sql(upgrade)
            conn.exec_driver_sql(upgrade)
            conn.commit()

    def test_recreate_map_analytics_preserves_version_history(self):
        self.assertEqual(self.post('send-raid-state', self.raid).status_code, 200)
        self.assertEqual(self.post('check-version', self.version_body).status_code, 404)
        script = (Path(__file__).parents[1] / 'sql/migrations/20261019_recreate_where_am_i_map_analytics.sql').read_text()
        with self.engine.connect() as conn:
            conn.exec_driver_sql(script)
            conn.exec_driver_sql(script)
            conn.commit()
        with self.sessions() as session:
            self.assertEqual(list(session.scalars(select(RaidStateEvent))), [])
            self.assertEqual(list(session.scalars(select(DesktopApiFailure))), [])
            self.assertEqual(len(list(session.scalars(select(VersionCheckEvent)))), 1)
            columns = list(session.scalars(text("select column_name from information_schema.columns where table_name='where_am_i_raid_state_events' order by ordinal_position")))
            self.assertEqual(columns[columns.index('map_slug')+1], 'requested_map')
        self.assertEqual(self.post('send-raid-state', self.raid).status_code, 200)

    def test_alias_resolution_preserves_original_and_forwards_canonical_map(self):
        with self.sessions.begin() as session:
            session.add(MapAlias(alias='new_woods', map_slug='woods'))
        raw = ' NEW_WOODS_preset '
        with self.client.websocket_connect('/ws') as socket:
            self.until(socket, 'location_connection_status')
            self.assertEqual(self.post('send-raid-state', dict(self.raid, map=raw)).status_code, 200)
            build_event = self.until(socket, 'wpf_raid_state')
            self.assertEqual(build_event['payload']['map'], 'woods')
            self.assertEqual(build_event['payload']['raid_ends_at'], self.raid['raid_ends_at'].replace('+00:00','Z'))
        with self.sessions() as session:
            row = session.scalars(select(RaidStateEvent)).one()
            self.assertEqual(row.requested_map, raw)
            self.assertEqual(row.map_slug, 'woods')

    def test_new_db_slug_is_available_without_restart(self):
        request = dict(self.raid, map='Icebreaker')
        self.assertEqual(self.post('send-raid-state', request).status_code, 422)
        with self.sessions.begin() as session:
            session.add(MapAlias(alias='Icebreaker', map_slug='icebreaker'))
        with self.client.websocket_connect('/ws') as socket:
            self.until(socket, 'location_connection_status')
            self.assertEqual(self.post('send-raid-state', request).status_code, 200)
            self.assertEqual(self.until(socket, 'wpf_raid_state')['payload']['map'], 'icebreaker')
        with self.sessions() as session:
            build_event = session.scalars(select(RaidStateEvent)).one()
            self.assertEqual(build_event.requested_map, 'Icebreaker')
            self.assertEqual(build_event.map_slug, 'icebreaker')
        self.assertEqual(self.post('send-raid-state', dict(request, map='icebreaker')).status_code, 200)
        with self.sessions.begin() as session:
            session.get(MapAlias, 'Icebreaker').is_active = False
        self.assertEqual(self.post('send-raid-state', request).status_code, 422)

    def test_unresolved_loading_is_collected_and_active_alias_updates_take_effect(self):
        loading = {'email':'owner@example.test', 'map':'future_factory_preset', 'started_at':None,
                       'is_active':False, 'timer_observed_at':None, 'raid_ends_at':None}
        self.assertEqual(self.post('send-raid-state', loading).status_code, 200)
        key = latest_key('owner@example.test') + ':raid'
        self.assertIsNone(json.loads(self.redis_server.get(key))['payload']['map'])
        with self.sessions() as session:
            row = session.scalars(select(RaidStateEvent)).one()
            self.assertEqual(row.requested_map, 'future_factory_preset')
            self.assertIsNone(row.map_slug)
        with self.sessions.begin() as session:
            session.add(MapAlias(alias='future_factory', map_slug='factory', is_active=False))
        self.assertEqual(self.post('send-raid-state', loading).status_code, 200)
        self.assertIsNone(json.loads(self.redis_server.get(key))['payload']['map'])
        with self.sessions.begin() as session:
            session.get(MapAlias, 'future_factory').is_active = True
        self.assertEqual(self.post('send-raid-state', loading).status_code, 200)
        payload = json.loads(self.redis_server.get(key))['payload']
        self.assertEqual(payload['map'], 'factory')
        self.assertFalse(payload['is_active'])
        self.assertIsNone(payload['raid_ends_at'])

    def test_alias_defaults_preserve_operator_changes_and_canonical_request(self):
        with self.sessions.begin() as session:
            session.add(MapAlias(alias='factory4_day', map_slug='woods', is_active=False))
        seed = (Path(__file__).parents[1] / 'sql/migrations/20261019_where_am_i_default_aliases.sql').read_text()
        with self.engine.connect() as conn:
            conn.exec_driver_sql(seed)
            conn.exec_driver_sql(seed)
            conn.commit()
        with self.sessions() as session:
            self.assertFalse(session.get(MapAlias, 'factory4_day').is_active)
            self.assertEqual(session.get(MapAlias, 'factory4_night').map_slug, 'factory')
        loading = {'email':'owner@example.test', 'map':'factory4_night', 'is_active':False}
        self.assertEqual(self.post('send-raid-state', loading).status_code, 200)
        payload = json.loads(self.redis_server.get(latest_key('owner@example.test') + ':raid'))['payload']
        self.assertEqual(payload['map'], 'factory')

    def test_alias_lookup_failure_is_not_success_and_keeps_raw_input(self):
        request = dict(self.raid, map='new_alias')
        with patch('api.where_am_i.service.resolve_map_slug', side_effect=OperationalError('offline', None, Exception())):
            api_response = self.post('send-raid-state', request)
        self.assertEqual(api_response.status_code, 503)
        self.assertEqual(api_response.json()['detail'], 'RAID_MAP_LOOKUP_UNAVAILABLE')
        self.assertIsNone(self.redis_server.get(latest_key('owner@example.test') + ':raid'))
        with self.sessions() as session:
            row = session.scalars(select(RaidStateEvent)).one()
            self.assertEqual(row.requested_map, 'new_alias')
            self.assertIsNone(row.map_slug)
            self.assertFalse(row.is_success)

    def test_raid_event_email_normalization_and_additive_migration(self):
        upgrade = (Path(__file__).parents[1] / 'sql/migrations/20261019_where_am_i_raid_event_email.sql').read_text()
        with self.engine.connect() as conn:
            conn.exec_driver_sql(upgrade)
            conn.exec_driver_sql(upgrade)
            conn.commit()
        self.assertEqual(self.post('send-raid-state', dict(self.raid, email='owner@example.test]')).status_code, 200)
        with self.sessions() as session:
            row = session.scalars(select(RaidStateEvent)).one()
            self.assertEqual(row.email, 'owner@example.test')
        cached = json.loads(self.redis_server.get(latest_key('owner@example.test') + ':raid'))
        self.assertNotIn('email', cached['payload'])
