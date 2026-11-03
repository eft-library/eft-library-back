"""API + authoritative PostgreSQL migration, against an isolated temporary server."""
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from api.where_am_i.path_reports import PathReport
from api.where_am_i.where_am_i_router import router
from database import Database


@unittest.skipUnless(importlib.util.find_spec('pgserver'), 'Install pgserver for isolated PostgreSQL tests')
class PathReportsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pgserver
        cls.root = tempfile.TemporaryDirectory(prefix='path-reports-v3-')
        cls.addClassCleanup(cls.root.cleanup)
        cls.server = pgserver.get_server(Path(cls.root.name) / 'postgres', cleanup_mode='delete')
        cls.addClassCleanup(cls.server.cleanup)
        cls.engine = create_engine(cls.server.get_uri())
        cls.addClassCleanup(cls.engine.dispose)
        root = Path(__file__).parents[1]
        source = (root / 'platform_db.sql').read_text()
        definition = re.search(r'create table if not exists where_am_i_path_reports \(.*?\n\);', source, re.S).group()
        migration = (root / 'sql/migrations/20261017_where_am_i_path_reports.sql').read_text()
        assert definition in migration
        # Run twice: the additive migration must be safe to rerun.
        with cls.engine.connect() as conn:
            conn.exec_driver_sql(migration)
            conn.exec_driver_sql(migration)
            conn.exec_driver_sql((root / 'sql/migrations/20261019_where_am_i_analytics.sql').read_text())
            conn.commit()
        cls.sessions = sessionmaker(cls.engine)

    def setUp(self):
        with self.engine.begin() as conn:
            conn.execute(text('truncate where_am_i_path_reports restart identity'))
            conn.execute(text('truncate where_am_i_api_failures restart identity'))
        patcher = patch.object(Database, 'SessionLocal', self.sessions)
        patcher.start()
        self.addCleanup(patcher.stop)
        app = FastAPI()
        app.include_router(router, prefix='/api/where-am-i')
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.body = {'path_type':'screenshot', 'path':r'D:\Games\Escape from Tarkov\Screenshots', 'app_version':'3.0.0'}

    def post(self, body):
        return self.client.post('/api/where-am-i/v3/path-reports', json=body)

    def test_independent_types_duplicates_and_literal_windows_paths(self):
        for kind, path in [('screenshot', self.body['path']), ('log', r'\\server\타르코프\Logs'),
                                 ('screenshot', self.body['path']), ('log', r'C:\Users\<user>\AppData\Local\Logs')]:
            result = self.post(dict(self.body, path_type=kind, path=path))
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json(), {'status':200,'msg':'OK','data':True})
        with self.sessions() as session:
            rows = list(session.scalars(select(PathReport).order_by(PathReport.id)))
            self.assertEqual(len(rows), 4)
            self.assertEqual(rows[0].path, rows[2].path)
            self.assertEqual(rows[1].path, r'\\server\타르코프\Logs')
            self.assertIsNotNone(rows[0].created_at.tzinfo)
            self.assertFalse(hasattr(rows[0], 'email'))

    def test_validation_and_length_boundaries(self):
        invalid = [{'path_type':'other'}, {'path_type':1}, {'path':''}, {'path':' \t '},
                      {'path':'x'*4097}, {'path':'x\x00y'}, {'path':'x\ny'}, {'path':123},
                      {'app_version':''}, {'app_version':' '*3}, {'app_version':'v'*65},
                      {'app_version':3}, {'email':'should-not-be-stored@example.test'}]
        for change in invalid:
            with self.subTest(change=change):
                self.assertEqual(self.post(dict(self.body, **change)).status_code, 422)
        for key in self.body:
            body = dict(self.body)
            del body[key]
            self.assertEqual(self.post(body).status_code, 422)
        self.assertEqual(self.post(dict(self.body, path='x'*4096, app_version='v'*64)).status_code, 200)
        with self.sessions() as session:
            self.assertEqual(len(list(session.scalars(select(PathReport)))), 1)
            failures = session.execute(text('select result_code, error_fields from where_am_i_api_failures')).mappings().all()
            self.assertEqual(len(failures), len(invalid) + len(self.body))
            self.assertTrue(all(row['result_code'] == 'REQUEST_VALIDATION_ERROR' for row in failures))
            self.assertNotIn('should-not-be-stored@example.test', str(failures))

    def test_storage_failure_is_not_success_and_does_not_log_path(self):
        with patch.object(self.sessions, 'begin', side_effect=OperationalError('secret path', None, Exception('offline'))):
            with self.assertLogs('api.where_am_i.path_reports', level='WARNING') as logs:
                result = self.post(self.body)
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.json(), {'detail':'PATH_REPORT_STORAGE_UNAVAILABLE'})
        self.assertNotIn('secret path', '\n'.join(logs.output))
        self.assertNotIn(self.body['path'], '\n'.join(logs.output))

    def test_database_rejects_invalid_kind_and_read_endpoint_absent(self):
        from sqlalchemy.exc import IntegrityError
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as conn:
                conn.execute(text("insert into where_am_i_path_reports(path_type,path,app_version) values ('invalid','x','v')"))
        self.assertEqual(self.client.get('/api/where-am-i/v3/path-reports').status_code, 405)
