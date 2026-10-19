"""Internal raid baseline lookup with isolated PostgreSQL, no network API calls."""
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from api.live_map.live_map_router import router
from database import V3Database


@unittest.skipUnless(importlib.util.find_spec('pgserver'), 'Install pgserver for isolated PostgreSQL tests')
class RaidDurationTestV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pgserver
        cls.directory_v3 = tempfile.TemporaryDirectory(prefix='raid-duration-v3-')
        cls.addClassCleanup(cls.directory_v3.cleanup)
        cls.server_v3 = pgserver.get_server(Path(cls.directory_v3.name) / 'postgres', cleanup_mode='delete')
        cls.addClassCleanup(cls.server_v3.cleanup)
        cls.engine_v3 = create_engine(cls.server_v3.get_uri())
        cls.addClassCleanup(cls.engine_v3.dispose)
        source_v3 = (Path(__file__).parents[1] / 'platform_db.sql').read_text()
        with cls.engine_v3.begin() as conn_v3:
            for name_v3 in ('maps', 'live_map_btr_routes'):
                ddl_v3 = re.search(rf'create table if not exists {name_v3}\s*\(.*?\n\);', source_v3, re.S).group()
                conn_v3.exec_driver_sql(ddl_v3)
        cls.sessions_v3 = sessionmaker(cls.engine_v3)

    def setUp(self):
        with self.engine_v3.begin() as conn_v3:
            conn_v3.execute(text('truncate maps, live_map_btr_routes'))
            conn_v3.execute(text("insert into maps(id,normalized_name,is_use) values ('woods-id','woods',true),('customs-id','customs',true)"))
        patcher_v3 = patch.object(V3Database, 'SessionLocal', self.sessions_v3)
        patcher_v3.start()
        self.addCleanup(patcher_v3.stop)
        # Any accidental return to the old upstream dependency fails this test.
        patcher_v3 = patch('requests.post', side_effect=AssertionError('External API must not be called'))
        patcher_v3.start()
        self.addCleanup(patcher_v3.stop)
        app_v3 = FastAPI()
        app_v3.include_router(router, prefix='/api/live-map')
        self.client_v3 = TestClient(app_v3)
        self.addCleanup(self.client_v3.close)

    def route_v3(self, name_v3, seconds_v3, enabled_v3=True):
        with self.engine_v3.begin() as conn_v3:
            conn_v3.execute(text('''insert into live_map_btr_routes(id,map_id,name,raid_duration_seconds,is_use)
                                    values (:id,'woods-id',:id,:seconds,:enabled)'''),
                            {'id':name_v3,'seconds':seconds_v3,'enabled':enabled_v3})

    def get_v3(self, name_v3='woods'):
        return self.client_v3.get('/api/live-map/v3/raid-duration/' + name_v3)

    def test_internal_baseline_and_live_updates_v3(self):
        self.route_v3('first', 2100)
        self.route_v3('same', 2100)
        self.route_v3('disabled', 3000, False)
        response_v3 = self.get_v3()
        self.assertEqual(response_v3.status_code, 200)
        self.assertEqual(response_v3.json(), {'status':200,'msg':'OK','data':{'normalized_name':'woods','minutes':35}})
        with self.engine_v3.begin() as conn_v3:
            conn_v3.execute(text('update live_map_btr_routes set raid_duration_seconds=2400 where is_use'))
        self.assertEqual(self.get_v3().json()['data']['minutes'], 40)

    def test_missing_ambiguous_invalid_and_database_failure_v3(self):
        self.assertEqual(self.get_v3('missing').json()['data'], None)
        self.assertEqual(self.get_v3('customs').json()['data'], None)
        self.route_v3('first', 2100)
        self.route_v3('different', 2400)
        self.assertEqual(self.get_v3().json(), {'status':200,'msg':'FAIL','data':None})
        with self.engine_v3.begin() as conn_v3:
            conn_v3.execute(text('update live_map_btr_routes set raid_duration_seconds=0'))
        self.assertIsNone(self.get_v3().json()['data'])
        with patch.object(V3Database, 'SessionLocal', side_effect=OperationalError('offline', None, Exception())):
            self.assertEqual(self.get_v3().json()['msg'], 'FAIL')
