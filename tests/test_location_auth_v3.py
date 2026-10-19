import os
import unittest
from unittest.mock import Mock, patch

import requests
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from util.location_auth_v3 import authenticate_location_socket_v3


class LocationAuthTestsV3(unittest.TestCase):
    def setUp(self):
        self.app_v3 = FastAPI()

        @self.app_v3.websocket('/ws')
        async def endpoint_v3(socket_v3: WebSocket, token: str):
            email_v3 = await authenticate_location_socket_v3(socket_v3, token)
            if email_v3:
                await socket_v3.accept()
                await socket_v3.send_json({'email': email_v3})
                await socket_v3.close()

    def connect_v3(self, response_v3=None, error_v3=None):
        with patch.dict(os.environ, {'GOOGLE_TOKEN_INFO_URL': 'https://auth.example.test/tokeninfo'}), \
             patch('util.location_auth_v3.requests.get', return_value=response_v3, side_effect=error_v3) as request_v3, \
             TestClient(self.app_v3) as client_v3:
            with client_v3.websocket_connect('/ws?token=test-token') as socket_v3:
                packet_v3 = socket_v3.receive_json()
                close_v3 = socket_v3.receive()
            request_v3.assert_called_once_with('https://auth.example.test/tokeninfo', params={'access_token': 'test-token'}, timeout=5)
            return packet_v3, close_v3['code']

    def test_valid_token_reaches_subscription_handler_v3(self):
        packet_v3, code_v3 = self.connect_v3(Mock(status_code=200, json=lambda: {'email': 'test@example.com'}))
        self.assertEqual(packet_v3, {'email': 'test@example.com'})
        self.assertEqual(code_v3, 1000)

    def test_invalid_token_requests_login_v3(self):
        for status_v3 in (400, 401):
            with self.subTest(status=status_v3):
                packet_v3, code_v3 = self.connect_v3(Mock(status_code=status_v3))
                self.assertEqual(packet_v3['status'], 'auth-required')
                self.assertEqual(code_v3, 4401)

    def test_provider_outage_remains_retryable_v3(self):
        for status_v3 in (403, 429, 500, 503):
            with self.subTest(status=status_v3):
                packet_v3, code_v3 = self.connect_v3(Mock(status_code=status_v3))
                self.assertEqual(packet_v3['status'], 'reconnecting')
                self.assertEqual(code_v3, 1013)
        for error_v3 in (requests.Timeout(), requests.ConnectionError()):
            packet_v3, code_v3 = self.connect_v3(error_v3=error_v3)
            self.assertEqual(code_v3, 1013)

    def test_malformed_provider_response_is_not_logout_v3(self):
        for value_v3 in ({}, [], {'email': None}):
            packet_v3, code_v3 = self.connect_v3(Mock(status_code=200, json=lambda: value_v3))
            self.assertEqual(code_v3, 1013)
