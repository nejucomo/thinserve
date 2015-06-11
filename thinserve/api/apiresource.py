import os
import json
from functable import FunctionTableProperty
from twisted.internet import defer
from twisted.web import resource, server
from thinserve.proto import session, error


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
    def __init__(self, createsession):
        self._createsession = createsession
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

        @d.addErrback
        def response_failed(failure):
            if isinstance(failure.value, error.ProtocolError):
                return failure
            else:
                failure.printTraceback()
                raise error.InternalError()

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
        msg = self._parse_json(req.content.read())

        s = self._get_session(req)
        if s is None:
            try:
                [opname, params] = msg
            except ValueError:
                raise error.MalformedMessage()
            if opname != 'create_session':
                raise error.MalformedMessage()
            else:
                # SECURITY BUG: params may contain 'self'. Protect the
                # app from this case.
                d = defer.maybeDeferred(self._createsession, **params)

                @d.addCallback
                def handle_app_instance(obj):
                    sid = os.urandom(self._SessionIdBytes).encode("hex")
                    self._sessions[sid] = session.Session(obj)
                    return {'session': sid}

                return d
        else:
            s.receive_message(msg)
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

    @staticmethod
    def _parse_json(text):
        try:
            return json.loads(text)
        except ValueError:
            raise error.MalformedJSON()
