import json
from unittest import TestCase
from twisted.web import server
from mock import MagicMock, call, patch
from thinserve.api.apiresource import ThinAPIResource
from thinserve.tests.testutil import check_mock


class ThinAPIResourceTests (TestCase):
    @patch('thinserve.proto.session.Session')
    def test_POST_create_session(self, m_Session):
        sid = 'FAKE_SESSION_ID'
        m_Session.return_value.id = sid
        m_apiroot = MagicMock(name='apiroot')
        m_request = MagicMock(name='Request')
        m_request.method = 'POST'
        m_request.content.read.return_value = '["create_session", {}]'

        tar = ThinAPIResource(m_apiroot)
        r = tar.render(m_request)

        self.assertEqual(r, server.NOT_DONE_YET)

        self.assertEqual(
            m_Session.mock_calls,
            [call(m_apiroot)])

        self.assertEqual(
            m_apiroot.mock_calls,
            [])

        self.assertEqual(
            m_request.mock_calls,
            [call.content.read(),
             call.setResponseCode(200),
             call.setHeader('Content-Type', 'application/json'),
             call.write('{\n  "session": "FAKE_SESSION_ID"\n}'),
             call.finish()])

    def test_error_GET(self):
        m_apiroot = MagicMock(name='apiroot')
        m_request = MagicMock(name='Request')
        m_request.method = 'GET'
        m_request.content.read.return_value = ''

        tar = ThinAPIResource(m_apiroot)
        r = tar.render(m_request)

        self.assertEqual(r, server.NOT_DONE_YET)

        self.assertEqual(
            m_apiroot.mock_calls,
            [])

        self._check_request(
            m_request,
            400,
            {"template": "unsupported HTTP method \"{method}\"",
             "params": {"method": "GET"}})

    def _check_request(self, m_request, code, body):
        check_mock(
            self,
            m_request,
            [call.content.read(),
             call.setResponseCode(400),
             call.setHeader('Content-Type', 'application/json'),
             call.write(json.dumps(body, indent=2)),
             call.finish()])
