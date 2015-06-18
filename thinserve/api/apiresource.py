import os
import json
from functable import FunctionTableProperty
from twisted.internet import defer
from twisted.web import resource, server
from thinserve.proto import session, error
from thinserve.proto.lazyparser import LazyParser


class ThinAPIResource (resource.Resource):
    """ThinAPIResource is an RPC mechanism:

    HTTP POST bodies and all response bodies are JSON. HTTP errors
    represent protocol errors (such as malformed JSON), but not
    application errors.

    POST ./
    Body: ["create_session", {}]
    Reply: {"session": sessionid}
    Synopsis: Create a new Session. Sessions timeout if no HTTP requests
              are made to them.


    POST ./${sessionid}
    Body: < ["call",
             {"id": callid,
              "target": sid or null,
              "method": methodname,
              "params": {...params...}}]
          | ["reply",
             {"id": callid,
              "result": < ["data", returnvalue]
                        | ["error",
                           {"template": errortemplate,
                            "params": {...params...}}]
                        >}]>
    Reply: "ok"
    Synopsis: Deliver a call or reply.

    GET ./${sessionid}
    Reply: [messages...]
    Synopsis: Return pending messages (calls or replies as above). This
              request blocks until there are messages ready, or it times
              out, or an identical concurrent GET is received by the
              server.
    """
    def __init__(self, app_create_session):
        self._app_create_session = app_create_session
        self._sessions = {}

    def render(self, req):
        d = defer.Deferred()
        d.callback(None)

        @d.addCallback
        def process_method(_):
            try:
                handler = self._method_handlers[req.method]
            except KeyError:
                raise error.UnsupportedHTTPMethod(method=req.method)
            else:
                return handler(req)

        @d.addCallback
        def response_ok(response):
            req.setResponseCode(200)
            return response

        d.addErrback(error.InternalError.coerce_unexpected_failure)

        @d.addErrback
        def response_protocol_error(failure):
            failure.trap(error.ProtocolError)
            req.setResponseCode(400)
            return {'template': failure.type.Template,
                    'params': failure.value.params}

        @d.addCallback
        def send_response(response):
            req.setHeader('Content-Type', 'application/json')
            req.write(json.dumps(response, indent=2))
            req.finish()

        return server.NOT_DONE_YET

    _SessionIdBytes = 16  # 128 bits of entropy.
    _method_handlers = FunctionTableProperty('_handle_')

    @_method_handlers.register
    def _handle_GET(self, req):
        # BUG: What if the client sends a giant body?
        if req.content.read() != '':
            raise error.UnexpectedHTTPBody()
        else:
            s = self._get_session(req)
            if s is None:
                raise error.UnsupportedHTTPMethod(method='GET')
            else:
                return s.gather_outgoing_messages()

    @_method_handlers.register
    def _handle_POST(self, req):
        mp = self._make_message_parser(req.content.read())

        s = self._get_session(req)
        if s is None:
            return mp.apply_variant(create_session=self._create_session)
        else:
            s.receive_message(mp)
            return "ok"

    def _get_session(self, req):
        if req.postpath == []:
            return None

        try:
            [sessid] = req.postpath
        except ValueError:
            raise error.InvalidParameter(name='session')

        try:
            return self._sessions[sessid]
        except KeyError:
            raise error.InvalidParameter(name='session')

    def _create_session(self, mp):
        d = defer.maybeDeferred(mp.apply_struct, self._app_create_session)

        @d.addCallback
        def handle_app_instance(obj):
            sid = os.urandom(self._SessionIdBytes).encode("hex")
            self._sessions[sid] = session.Session(obj)
            return {'session': sid}

        return d

    @staticmethod
    def _make_message_parser(text):
        try:
            jdoc = json.loads(text)
        except ValueError:
            raise error.MalformedJSON()
        else:
            return LazyParser(jdoc)
