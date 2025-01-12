#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# Licensed under the GPLv3, see LICENSE file for details.

import io
import unittest
import urllib.error
from controlsocket import Client, APIError, ConnectionError


class TestClass(unittest.TestCase):
    def test_add_metrics_user_success(self):
        mock_opener = MockOpener(self)
        control_socket = Client('fake_socket_path', opener=mock_opener)

        mock_opener.expect(
            url='http://localhost/metrics-users',
            method='POST',
            body=r'{"username": "juju-metrics-r0", "password": "passwd"}',

            response=MockResponse(
                headers=MockHeaders(content_type='application/json'),
                body=r'{"message":"created user \"juju-metrics-r0\""}'
            )
        )
        control_socket.add_metrics_user('juju-metrics-r0', 'passwd')

    def test_add_metrics_user_fail(self):
        mock_opener = MockOpener(self)
        control_socket = Client('fake_socket_path', opener=mock_opener)

        mock_opener.expect(
            url='http://localhost/metrics-users',
            method='POST',
            body=r'{"username": "juju-metrics-r0", "password": "passwd"}',

            error=urllib.error.HTTPError(
                url='http://localhost/metrics-users',
                code=409,
                msg='',
                hdrs=None,
                fp=io.BytesIO(br'{"error":"user \"juju-metrics-r0\" already exists"}'),
            )
        )

        with self.assertRaises(APIError) as cm:
            control_socket.add_metrics_user('juju-metrics-r0', 'passwd')
        self.assertEqual(cm.exception.body, {'error': 'user "juju-metrics-r0" already exists'})
        self.assertEqual(cm.exception.code, 409)
        self.assertEqual(cm.exception.status, '')
        self.assertEqual(cm.exception.message, 'user "juju-metrics-r0" already exists')

    def test_remove_metrics_user_success(self):
        mock_opener = MockOpener(self)
        control_socket = Client('fake_socket_path', opener=mock_opener)

        mock_opener.expect(
            url='http://localhost/metrics-users/juju-metrics-r0',
            method='DELETE',
            body=None,

            response=MockResponse(
                headers=MockHeaders(content_type='application/json'),
                body=r'{"message":"deleted user \"juju-metrics-r0\""}'
            )
        )
        control_socket.remove_metrics_user('juju-metrics-r0')

    def test_remove_metrics_user_fail(self):
        mock_opener = MockOpener(self)
        control_socket = Client('fake_socket_path', opener=mock_opener)

        mock_opener.expect(
            url='http://localhost/metrics-users/juju-metrics-r0',
            method='DELETE',
            body=None,

            error=urllib.error.HTTPError(
                url='http://localhost/metrics-users/juju-metrics-r0',
                code=404,
                msg='',
                hdrs=None,
                fp=io.BytesIO(br'{"error":"user \"juju-metrics-r0\" not found"}'),
            )
        )

        with self.assertRaises(APIError) as cm:
            control_socket.remove_metrics_user('juju-metrics-r0')
        self.assertEqual(cm.exception.body, {'error': 'user "juju-metrics-r0" not found'})
        self.assertEqual(cm.exception.code, 404)
        self.assertEqual(cm.exception.status, '')
        self.assertEqual(cm.exception.message, 'user "juju-metrics-r0" not found')

    def test_connection_error(self):
        mock_opener = MockOpener(self)
        control_socket = Client('fake_socket_path', opener=mock_opener)

        mock_opener.expect(
            url='http://localhost/metrics-users',
            method='POST',
            body=r'{"username": "juju-metrics-r0", "password": "passwd"}',

            error=urllib.error.URLError('could not connect to socket')
        )

        with self.assertRaisesRegex(ConnectionError, 'could not connect to socket'):
            control_socket.add_metrics_user('juju-metrics-r0', 'passwd')


class MockOpener:
    def __init__(self, test_case):
        self.test = test_case

    def expect(self, url, method, body, response=None, error=None):
        self.url = url
        self.method = method
        self.body = body

        self.response = response
        self.error = error

    def open(self, request, timeout):
        self.test.assertEqual(request.full_url, self.url)
        self.test.assertEqual(request.method, self.method)
        if self.body is None:
            self.test.assertEqual(request.data, None)
        else:
            self.test.assertEqual(request.data.decode('utf-8'), self.body)

        if self.response:
            return self.response
        else:
            raise self.error


class MockResponse:
    def __init__(self, headers, body):
        self.headers = headers
        self.body = body

    def read(self):
        return self.body


class MockHeaders:
    def __init__(self, content_type, params=None):
        self.content_type = content_type
        self.params = params

    def get_content_type(self):
        return self.content_type

    def get_params(self):
        return self.params
