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
from database import Database


@unittest.skipUnless(importlib.util.find_spec('pgserver'), 'Install pgserver for isolated PostgreSQL tests')
class RaidDurationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pgserver
        cls.directory = tempfile.TemporaryDirectory(prefix='raid-duration-v3-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.server = pgserver.get_server(Path(cls.directory.name) / 'postgres', cleanup_mode='delete')
        cls.addClassCleanup(cls.server.cleanup)
        cls.engine = create_engine(cls.server.get_uri())
        cls.addClassCleanup(cls.engine.dispose)
        source = (Path(__file__).parents[1] / 'platform_db.sql').read_text()
        with cls.engine.begin() as conn:
            for name in ('maps', 'live_map_btr_routes'):
                ddl = re.search(rf'create table if not exists {name}\s*\(.*?\n\);', source, re.S).group()
                conn.exec_driver_sql(ddl)
        cls.sessions = sessionmaker(cls.engine)

    def setUp(self):
        with self.engine.begin() as conn:
            conn.execute(text('truncate maps, live_map_btr_routes'))
            conn.execute(text("insert into maps(id,normalized_name,is_use) values ('woods-id','woods',true),('customs-id','customs',true)"))
        patcher = patch.object(Database, 'SessionLocal', self.sessions)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Any accidental return to the old upstream dependency fails this test.
        patcher = patch('requests.post', side_effect=AssertionError('External API must not be called'))
        patcher.start()
        self.addCleanup(patcher.stop)
        app = FastAPI()
        app.include_router(router, prefix='/api/live-map')
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def route(self, name, seconds, enabled=True):
        with self.engine.begin() as conn:
            conn.execute(text('''insert into live_map_btr_routes(id,map_id,name,raid_duration_seconds,is_use)
                                    values (:id,'woods-id',:id,:seconds,:enabled)'''),
                            {'id':name,'seconds':seconds,'enabled':enabled})

    def get(self, name='woods'):
        return self.client.get('/api/live-map/v3/raid-duration/' + name)

    def test_internal_baseline_and_live_updates(self):
        self.route('first', 2100)
        self.route('same', 2100)
        self.route('disabled', 3000, False)
        api_response = self.get()
        self.assertEqual(api_response.status_code, 200)
        self.assertEqual(api_response.json(), {'status':200,'msg':'OK','data':{'normalized_name':'woods','minutes':35}})
        with self.engine.begin() as conn:
            conn.execute(text('update live_map_btr_routes set raid_duration_seconds=2400 where is_use'))
        self.assertEqual(self.get().json()['data']['minutes'], 40)

    def test_missing_ambiguous_invalid_and_database_failure(self):
        self.assertEqual(self.get('missing').json()['data'], None)
        self.assertEqual(self.get('customs').json()['data'], None)
        self.route('first', 2100)
        self.route('different', 2400)
        self.assertEqual(self.get().json(), {'status':200,'msg':'FAIL','data':None})
        with self.engine.begin() as conn:
            conn.execute(text('update live_map_btr_routes set raid_duration_seconds=0'))
        self.assertIsNone(self.get().json()['data'])
        with patch.object(Database, 'SessionLocal', side_effect=OperationalError('offline', None, Exception())):
            self.assertEqual(self.get().json()['msg'], 'FAIL')
