"""Authentication errors must be visible as HTTP errors, never 200/FAIL or guest data."""
import os
import unittest
from unittest.mock import Mock, patch

import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.progress.progress_router import router as progress_router
from api.roadmap.roadmap_router import router as roadmap_router
from api.user.user_router import router as user_router


class HttpAuthTest(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(user_router, prefix='/api/user')
        app.include_router(progress_router, prefix='/api/progress')
        app.include_router(roadmap_router, prefix='/api/roadmap')
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        env = patch.dict(os.environ, {'GOOGLE_TOKEN_INFO_URL': 'https://auth.example.test/tokeninfo'})
        env.start()
        self.addCleanup(env.stop)
        upstream = patch('util.auth.requests.get', return_value=Mock(
            status_code=200, json=lambda: {'email': 'user@example.test'}))
        self.upstream = upstream.start()
        self.addCleanup(upstream.stop)
        self.headers = {'Authorization': 'Bearer test-token'}

    def user_info(self):
        return self.client.get('/api/user/v3/user-info', headers=self.headers)

    def test_valid_auth_preserves_success_and_bounds_upstream_wait(self):
        with patch('api.user.user_router.UserService.get_user', return_value={'email': 'user@example.test'}) as lookup:
            response = self.user_info()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['msg'], 'OK')
        lookup.assert_called_once_with('user@example.test')
        self.upstream.assert_called_once_with('https://auth.example.test/tokeninfo',
                                             params={'access_token': 'test-token'}, timeout=5)

    def test_expired_token_is_401_before_business_logic(self):
        for status in (400, 401):
            with self.subTest(status=status), patch('api.user.user_router.UserService.get_user') as lookup:
                self.upstream.return_value = Mock(status_code=status)
                response = self.user_info()
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json(), {'detail': 'INVALID_TOKEN'})
                self.assertEqual(response.headers['www-authenticate'], 'Bearer')
                lookup.assert_not_called()

    def test_upstream_rejection_and_outages_do_not_force_logout(self):
        for status in (403, 429, 500, 503):
            with self.subTest(status=status):
                self.upstream.return_value = Mock(status_code=status)
                response = self.user_info()
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json(), {'detail': 'AUTH_SERVICE_UNAVAILABLE'})

    def test_network_and_malformed_responses_are_503(self):
        for error in (requests.Timeout(), requests.ConnectionError()):
            with self.subTest(error=type(error).__name__):
                self.upstream.side_effect = error
                self.assertEqual(self.user_info().status_code, 503)
        self.upstream.side_effect = None
        for payload in (None, [], {}, {'email': None}, {'email': ''}, {'email': '  '}):
            with self.subTest(payload=payload):
                self.upstream.return_value = Mock(status_code=200, json=lambda: payload)
                self.assertEqual(self.user_info().status_code, 503)
        self.upstream.return_value = Mock(status_code=200)
        self.upstream.return_value.json.side_effect = ValueError('invalid JSON')
        self.assertEqual(self.user_info().status_code, 503)

    def test_unverified_email_is_401_and_missing_configuration_is_503(self):
        for key in ('verified_email', 'email_verified'):
            self.upstream.return_value = Mock(status_code=200, json=lambda: {'email':'user@example.test',key:False})
            self.assertEqual(self.user_info().status_code, 401)
        self.upstream.reset_mock()
        with patch.dict(os.environ, {'GOOGLE_TOKEN_INFO_URL': ''}):
            self.assertEqual(self.user_info().status_code, 503)
        self.upstream.assert_not_called()

    def test_anonymous_reads_remain_available_without_upstream_auth(self):
        for path, target in (
            ('/api/progress/v3/progress-item', 'api.progress.progress_router.ProgressService.get_user_progress'),
            ('/api/roadmap/v3/get-user-roadmap', 'api.roadmap.roadmap_router.RoadmapService.get_user_roadmap'),
        ):
            with self.subTest(path=path), patch(target, return_value=[]) as lookup:
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['msg'], 'OK')
                lookup.assert_called_once_with(None)
        self.upstream.assert_not_called()

    def test_supplied_invalid_credentials_never_fall_back_to_guest(self):
        self.upstream.return_value = Mock(status_code=401)
        for path, target in (
            ('/api/progress/v3/progress-item', 'api.progress.progress_router.ProgressService.get_user_progress'),
            ('/api/roadmap/v3/get-user-roadmap', 'api.roadmap.roadmap_router.RoadmapService.get_user_roadmap'),
        ):
            for authorization in ('Bearer expired', 'Bearer ', 'Basic invalid', ''):
                with self.subTest(path=path,authorization=authorization), patch(target) as lookup:
                    response = self.client.get(path, headers={'Authorization': authorization})
                    self.assertEqual(response.status_code, 401)
                    lookup.assert_not_called()

    def test_write_requires_authentication_and_is_not_executed_on_failure(self):
        for path, payload, target in (
            ('/api/progress/v3/update-progress-item', {'userRebirth':[],'userKappa':[]},
             'api.progress.progress_router.ProgressService.update_progress'),
            ('/api/roadmap/v3/save-roadmap', {'questList':[]},
             'api.roadmap.roadmap_router.RoadmapService.save_roadmap'),
        ):
            with self.subTest(path=path), patch(target) as save:
                response = self.client.post(path,json=payload)
                self.assertEqual(response.status_code,401)
                self.upstream.return_value = Mock(status_code=401)
                response = self.client.post(path,json=payload,headers=self.headers)
                self.assertEqual(response.status_code,401)
                save.assert_not_called()

    def test_user_lookup_failure_and_missing_user_are_not_auth_expiry(self):
        with patch('api.user.service.Database.SessionLocal',side_effect=RuntimeError('database unavailable')), \
             self.assertLogs('api.user',level='ERROR'):
            response = self.user_info()
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json(),{'detail':'USER_LOOKUP_UNAVAILABLE'})
        with patch('api.user.user_router.UserService.get_user',return_value=None):
            response = self.user_info()
        self.assertEqual(response.status_code,404)
        self.assertEqual(response.json(),{'detail':'USER_NOT_FOUND'})

    def test_missing_required_token_is_401_without_contacting_provider(self):
        response = self.client.get('/api/user/v3/user-info')
        self.assertEqual(response.status_code,401)
        self.assertEqual(response.headers['www-authenticate'],'Bearer')
        self.upstream.assert_not_called()
