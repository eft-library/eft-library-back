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

from api.where_am_i.path_reports_v3 import PathReportV3
from api.where_am_i.where_am_i_router import router
from database import V3Database


@unittest.skipUnless(importlib.util.find_spec('pgserver'), 'Install pgserver for isolated PostgreSQL tests')
class PathReportsTestV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pgserver
        cls.root_v3 = tempfile.TemporaryDirectory(prefix='path-reports-v3-')
        cls.addClassCleanup(cls.root_v3.cleanup)
        cls.server_v3 = pgserver.get_server(Path(cls.root_v3.name) / 'postgres', cleanup_mode='delete')
        cls.addClassCleanup(cls.server_v3.cleanup)
        cls.engine_v3 = create_engine(cls.server_v3.get_uri())
        cls.addClassCleanup(cls.engine_v3.dispose)
        root_v3 = Path(__file__).parents[1]
        source_v3 = (root_v3 / 'platform_db.sql').read_text()
        definition_v3 = re.search(r'create table if not exists where_am_i_path_reports \(.*?\n\);', source_v3, re.S).group()
        migration_v3 = (root_v3 / 'sql/migrations/20261017_where_am_i_path_reports.sql').read_text()
        assert definition_v3 in migration_v3
        # Run twice: the additive migration must be safe to rerun.
        with cls.engine_v3.connect() as conn_v3:
            conn_v3.exec_driver_sql(migration_v3)
            conn_v3.exec_driver_sql(migration_v3)
            conn_v3.exec_driver_sql((root_v3 / 'sql/migrations/20261019_where_am_i_analytics.sql').read_text())
            conn_v3.commit()
        cls.sessions_v3 = sessionmaker(cls.engine_v3)

    def setUp(self):
        with self.engine_v3.begin() as conn_v3:
            conn_v3.execute(text('truncate where_am_i_path_reports restart identity'))
            conn_v3.execute(text('truncate where_am_i_api_failures restart identity'))
        patcher_v3 = patch.object(V3Database, 'SessionLocal', self.sessions_v3)
        patcher_v3.start()
        self.addCleanup(patcher_v3.stop)
        app_v3 = FastAPI()
        app_v3.include_router(router, prefix='/api/where-am-i')
        self.client_v3 = TestClient(app_v3)
        self.addCleanup(self.client_v3.close)
        self.body_v3 = {'path_type':'screenshot', 'path':r'D:\Games\Escape from Tarkov\Screenshots', 'app_version':'3.0.0'}

    def post_v3(self, body_v3):
        return self.client_v3.post('/api/where-am-i/v3/path-reports', json=body_v3)

    def test_independent_types_duplicates_and_literal_windows_paths_v3(self):
        for kind_v3, path_v3 in [('screenshot', self.body_v3['path']), ('log', r'\\server\타르코프\Logs'),
                                 ('screenshot', self.body_v3['path']), ('log', r'C:\Users\<user>\AppData\Local\Logs')]:
            result_v3 = self.post_v3(dict(self.body_v3, path_type=kind_v3, path=path_v3))
            self.assertEqual(result_v3.status_code, 200)
            self.assertEqual(result_v3.json(), {'status':200,'msg':'OK','data':True})
        with self.sessions_v3() as session_v3:
            rows_v3 = list(session_v3.scalars(select(PathReportV3).order_by(PathReportV3.id)))
            self.assertEqual(len(rows_v3), 4)
            self.assertEqual(rows_v3[0].path, rows_v3[2].path)
            self.assertEqual(rows_v3[1].path, r'\\server\타르코프\Logs')
            self.assertIsNotNone(rows_v3[0].created_at.tzinfo)
            self.assertFalse(hasattr(rows_v3[0], 'email'))

    def test_validation_and_length_boundaries_v3(self):
        invalid_v3 = [{'path_type':'other'}, {'path_type':1}, {'path':''}, {'path':' \t '},
                      {'path':'x'*4097}, {'path':'x\x00y'}, {'path':'x\ny'}, {'path':123},
                      {'app_version':''}, {'app_version':' '*3}, {'app_version':'v'*65},
                      {'app_version':3}, {'email':'should-not-be-stored@example.test'}]
        for change_v3 in invalid_v3:
            with self.subTest(change_v3=change_v3):
                self.assertEqual(self.post_v3(dict(self.body_v3, **change_v3)).status_code, 422)
        for key_v3 in self.body_v3:
            body_v3 = dict(self.body_v3)
            del body_v3[key_v3]
            self.assertEqual(self.post_v3(body_v3).status_code, 422)
        self.assertEqual(self.post_v3(dict(self.body_v3, path='x'*4096, app_version='v'*64)).status_code, 200)
        with self.sessions_v3() as session_v3:
            self.assertEqual(len(list(session_v3.scalars(select(PathReportV3)))), 1)
            failures_v3 = session_v3.execute(text('select result_code, error_fields from where_am_i_api_failures')).mappings().all()
            self.assertEqual(len(failures_v3), len(invalid_v3) + len(self.body_v3))
            self.assertTrue(all(row_v3['result_code'] == 'REQUEST_VALIDATION_ERROR' for row_v3 in failures_v3))
            self.assertNotIn('should-not-be-stored@example.test', str(failures_v3))

    def test_storage_failure_is_not_success_and_does_not_log_path_v3(self):
        with patch.object(self.sessions_v3, 'begin', side_effect=OperationalError('secret path', None, Exception('offline'))):
            with self.assertLogs('api.where_am_i.path_reports_v3', level='WARNING') as logs_v3:
                result_v3 = self.post_v3(self.body_v3)
        self.assertEqual(result_v3.status_code, 503)
        self.assertEqual(result_v3.json(), {'detail':'PATH_REPORT_STORAGE_UNAVAILABLE'})
        self.assertNotIn('secret path', '\n'.join(logs_v3.output))
        self.assertNotIn(self.body_v3['path'], '\n'.join(logs_v3.output))

    def test_database_rejects_invalid_kind_and_read_endpoint_absent_v3(self):
        from sqlalchemy.exc import IntegrityError
        with self.assertRaises(IntegrityError):
            with self.engine_v3.begin() as conn_v3:
                conn_v3.execute(text("insert into where_am_i_path_reports(path_type,path,app_version) values ('invalid','x','v')"))
        self.assertEqual(self.client_v3.get('/api/where-am-i/v3/path-reports').status_code, 405)
