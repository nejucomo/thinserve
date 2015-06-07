import json
from unittest import TestCase
from twisted.web import server
from mock import MagicMock, call, patch
from thinserve.api.apiresource import ThinAPIResource
from thinserve.tests.testutil import check_mock


class ThinAPIResourceTests (TestCase):
    def setUp(self):
        self.m_apiroot = MagicMock(name='apiroot')
        self.tar = ThinAPIResource(self.m_apiroot)
        self.m_request = None

    @patch('thinserve.proto.session.Session')
    def test_POST_create_session(self, m_Session):
        sid = 'FAKE_SESSION_ID'
        m_Session.return_value.id = sid

        self._make_request(
            'POST',
            ["create_session", {}],
            200,
            {"session": sid})

        self.assertEqual(
            self.m_apiroot.mock_calls,
            [])

        self.assertEqual(
            m_Session.mock_calls,
            [call(self.m_apiroot)])

    def test_error_GET(self):
        self._make_request(
            'GET',
            None,
            400,
            {"template": "unsupported HTTP method \"{method}\"",
             "params": {"method": "GET"}})

        self.assertEqual(
            self.m_apiroot.mock_calls,
            [])

    # Helper code:
    def _make_request(self, method, reqbody, rescode, resbody):
        m_request = MagicMock(name='Request')
        m_request.method = method
        if reqbody is None:
            readrv = ''
        else:
            readrv = json.dumps(reqbody, indent=2)

        m_request.content.read.return_value = readrv

        r = self.tar.render(m_request)

        self.assertEqual(r, server.NOT_DONE_YET)

        check_mock(
            self,
            m_request,
            [call.content.read(),
             call.setResponseCode(rescode),
             call.setHeader('Content-Type', 'application/json'),
             call.write(json.dumps(resbody, indent=2)),
             call.finish()])
