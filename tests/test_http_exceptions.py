"""HTTP response and per-request isolation contracts for the shared error catalog."""
import unittest

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from util.http_exceptions import HttpError


class HttpErrorTest(unittest.TestCase):
    def test_authentication_and_retry_headers_reach_http_response(self):
        app = FastAPI()

        @app.get('/auth')
        def authenticate():
            raise HttpError.INVALID_TOKEN.exception(headers={'WWW-Authenticate': 'Bearer'})

        @app.get('/rate')
        def rate_limit():
            raise HttpError.TOO_MANY_ATTEMPTS.exception(headers={'Retry-After': '37'})

        with TestClient(app) as client:
            response = client.get('/auth')
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json(), {'detail': 'INVALID_TOKEN'})
            self.assertEqual(response.headers['www-authenticate'], 'Bearer')
            response = client.get('/rate')
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.json(), {'detail': 'TOO_MANY_ATTEMPTS'})
            self.assertEqual(response.headers['retry-after'], '37')

    def test_exceptions_and_headers_are_not_shared_between_requests(self):
        headers = {'Retry-After': '30'}
        first = HttpError.TOO_MANY_ATTEMPTS.exception(headers=headers)
        headers['Retry-After'] = '100'
        second = HttpError.TOO_MANY_ATTEMPTS.exception(headers={'Retry-After': '60'})
        self.assertIsNot(first, second)
        self.assertEqual(first.headers, {'Retry-After': '30'})
        self.assertEqual(second.headers, {'Retry-After': '60'})
        self.assertIsNone(HttpError.TOO_MANY_ATTEMPTS.exception().headers)
        try:
            raise first
        except HTTPException as error:
            self.assertIs(error, first)
        self.assertIsNone(second.__traceback__)

    def test_upload_error_keeps_dynamic_reason_without_reformatting_it(self):
        reason = ValueError('bad image {width}: 한글')
        error = HttpError.IMAGE_PROCESSING_FAILED_WITH_REASON.exception(error=reason)
        self.assertEqual(error.status_code, 500)
        self.assertEqual(error.detail, '이미지 처리 실패: bad image {width}: 한글')
        self.assertEqual(HttpError.IMAGE_PROCESSING_FAILED.detail, '이미지 처리 실패')
