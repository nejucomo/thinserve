import itertools
from functable import FunctionTableProperty
from twisted.internet import defer
from thinserve.api.referenceable import Referenceable
from thinserve.api.remerr import RemoteError
from thinserve.proto.shuttle import Shuttle


class Session (object):
    def __init__(self, rootobj):
        assert Referenceable._check(rootobj), \
            'The root object must be @Referenceable.'
        self._rootobj = rootobj
        self._pendingcalls = {}
        self._idgen = itertools.count(0)
        self._shuttle = Shuttle()

    def gather_outgoing_messages(self):
        d = defer.Deferred()
        self._shuttle.gather_messages(d)
        return d

    def receive_message(self, msg):
        msg.apply_variant_struct(**self._receivers)

    _receivers = FunctionTableProperty('_receive_')

    @_receivers.register
    def _receive_call(self, id, target, method):
        id = id.parse_type(int)
        obj = self._resolve_sref(target.unwrap())
        methods = Referenceable._get_bound_methods(obj)

        d = defer.maybeDeferred(method.apply_variant_struct, **methods)
        d.addCallback(lambda r: ['data', r])
        d.addErrback(lambda f: ['error', f])
        d.addCallback(lambda reply: self._send_reply(id, reply))

    @_receivers.register
    def _receive_reply(self, id, result):
        id = id.parse_type(int)

        d = self._pendingcalls.pop(id)

        result.apply_variant(
            data=d.callback,
            error=lambda lp: d.errback(RemoteError(lp)))

    def _send_call(self, target, method, params):
        callid = self._idgen.next()

        self._shuttle.send_message(
            ['call',
             {'id': callid,
              'target': target,
              'method': [method, params]}])

        d = defer.Deferred()
        self._pendingcalls[callid] = d
        return d

    def _send_reply(self, id, result):
        self._shuttle.send_message(
            ['reply',
             {'id': id, 'result': result}])

    def _resolve_sref(self, sref):
        if sref is None:
            return self._rootobj
        else:
            raise NotImplementedError(sref)
