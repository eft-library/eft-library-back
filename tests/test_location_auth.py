import os
import unittest
from unittest.mock import Mock, patch

import requests
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from util.location_auth import authenticate_location_socket


class LocationAuthTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()

        @self.app.websocket('/ws')
        async def endpoint(socket: WebSocket, token: str):
            email = await authenticate_location_socket(socket, token)
            if email:
                await socket.accept()
                await socket.send_json({'email': email})
                await socket.close()

    def connect(self, api_response=None, error=None):
        with patch.dict(os.environ, {'GOOGLE_TOKEN_INFO_URL': 'https://auth.example.test/tokeninfo'}), \
             patch('util.location_auth.requests.get', return_value=api_response, side_effect=error) as request, \
             TestClient(self.app) as client:
            with client.websocket_connect('/ws?token=test-token') as socket:
                socket_packet = socket.receive_json()
                close = socket.receive()
            request.assert_called_once_with('https://auth.example.test/tokeninfo', params={'access_token': 'test-token'}, timeout=5)
            return socket_packet, close['code']

    def test_valid_token_reaches_subscription_handler(self):
        socket_packet, code = self.connect(Mock(status_code=200, json=lambda: {'email': 'test@example.com'}))
        self.assertEqual(socket_packet, {'email': 'test@example.com'})
        self.assertEqual(code, 1000)

    def test_invalid_token_requests_login(self):
        for status in (400, 401):
            with self.subTest(status=status):
                socket_packet, code = self.connect(Mock(status_code=status))
                self.assertEqual(socket_packet['status'], 'auth-required')
                self.assertEqual(code, 4401)

    def test_provider_outage_remains_retryable(self):
        for status in (403, 429, 500, 503):
            with self.subTest(status=status):
                socket_packet, code = self.connect(Mock(status_code=status))
                self.assertEqual(socket_packet['status'], 'reconnecting')
                self.assertEqual(code, 1013)
        for error in (requests.Timeout(), requests.ConnectionError()):
            socket_packet, code = self.connect(error=error)
            self.assertEqual(code, 1013)

    def test_malformed_provider_response_is_not_logout(self):
        for value in ({}, [], {'email': None}):
            socket_packet, code = self.connect(Mock(status_code=200, json=lambda: value))
            self.assertEqual(code, 1013)
