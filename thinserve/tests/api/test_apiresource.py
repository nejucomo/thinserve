import json
from unittest import TestCase
from twisted.web import server
from mock import MagicMock, call, patch
from thinserve.api.apiresource import ThinAPIResource
from thinserve.tests.testutil import check_mock, EqCb


class ThinAPIResourceTests (TestCase):
    def setUp(self):
        self.m_createsession = MagicMock(name='createsession')
        self.tar = ThinAPIResource(self.m_createsession)
        self.m_request = None

    @patch('thinserve.proto.session.Session')
    @patch('os.urandom')
    def test_POST_create_session(self, m_urandom, m_Session):
        entropy = 'fake entropy'
        m_urandom.return_value = entropy

        self._make_request(
            'POST', [],
            ["create_session", {}],
            True, 200,
            {"session": entropy.encode("hex")})

        check_mock(
            self, self.m_createsession,
            [call()])

        check_mock(
            self, m_urandom,
            [call(ThinAPIResource._SessionIdBytes)])

        check_mock(
            self, m_Session,
            [call(self.m_createsession.return_value)])

    def test_GET_session_poll(self):
        sid = 'FAKE_SESSION_ID'
        msgs = ["WHEE!"]

        m_session = MagicMock(name='SessionInstance')
        m_session.return_value.id = sid
        m_session.gather_outgoing_messages.return_value = msgs

        # Peek behind the curtain to avoid covering sessio creation code:
        self.tar._sessions[sid] = m_session

        self._make_request(
            'GET', [sid],
            None,
            True, 200,
            msgs)

        check_mock(
            self, m_session,
            [call.gather_outgoing_messages()])

    def test_POST_session_message(self):
        sid = 'FAKE_SESSION_ID'
        msg = {"fruit": "banana"}

        m_session = MagicMock(name='SessionInstance')
        m_session.return_value.id = sid

        # Peek behind the curtain to avoid covering sessio creation code:
        self.tar._sessions[sid] = m_session

        self._make_request(
            'POST', [sid],
            msg,
            True, 200,
            'ok')

        check_mock(
            self, m_session,
            [call.receive_message(EqCb(lambda lp: lp.unwrap() == msg))])

    # Test many error input conditions:
    def test_unexpected_internal_error(self):
        # Violate the interface to cause an "unexpected" error:
        @self.tar._method_handlers.register
        def _handle_GET(req):
            assert False, 'Intentional test corruption.'

        self._make_request(
            'GET', [],
            None,
            False, 400,
            {"template": "internal error",
             "params": {}})

    def test_error_GET(self):
        self._make_request(
            'GET', [],
            None,
            True, 400,
            {"template": "unsupported HTTP method \"{method}\"",
             "params": {"method": "GET"}})

    def test_error_unsupported_method(self):
        self._make_request(
            'HEAD', [],
            None,
            False, 400,
            {"template": "unsupported HTTP method \"{method}\"",
             "params": {"method": "HEAD"}})

    def test_error_GET_with_body(self):
        self._make_request(
            'GET', [],
            'foobody',
            True, 400,
            {"template": "unexpected HTTP body",
             "params": {}})

    def test_error_POST_root_malformed_message(self):
        self._make_request(
            'POST', [],
            {"unexpected": "message"},
            True, 400,
            {"template": "malformed message",
             "params": {}})

    def test_error_POST_root_unknown_operation(self):
        self._make_request(
            'POST', [],
            ["create_disaster", 42],
            True, 400,
            {"template": "malformed message",
             "params": {}})

    def test_error_GET_bad_postpath(self):
        self._make_request(
            'GET', ['foo', 'bar'],
            None,
            True, 400,
            {"template": 'invalid parameter "{name}"',
             "params": {"name": "session"}})

    def test_error_GET_unknown_session(self):
        self._make_request(
            'GET', ['I am an unknown session id'],
            None,
            True, 400,
            {"template": 'invalid parameter "{name}"',
             "params": {"name": "session"}})

    def test_error_POST_malformed_json(self):
        self._make_request(
            'POST', [],
            'mangled JSON',
            True, 400,
            {"template": 'malformed JSON',
             "params": {}})

    # Helper code:
    def _make_request(
            self,
            method, postpath, reqbody,
            resreadsreq, rescode, resbody):

        m_request = MagicMock(name='Request')
        m_request.method = method
        m_request.postpath = postpath
        if reqbody is None:
            readrv = ''
        elif reqbody == 'mangled JSON':
            readrv = reqbody
        else:
            readrv = json.dumps(reqbody, indent=2)

        m_request.content.read.return_value = readrv

        r = self.tar.render(m_request)

        self.assertEqual(r, server.NOT_DONE_YET)

        expected = [
            call.setResponseCode(rescode),
            call.setHeader('Content-Type', 'application/json'),
            call.write(json.dumps(resbody, indent=2)),
            call.finish(),
        ]

        if resreadsreq:
            expected.insert(0, call.content.read())

        check_mock(self, m_request, expected)
