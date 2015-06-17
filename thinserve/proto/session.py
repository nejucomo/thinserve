from functable import FunctionTableProperty
from twisted.internet import defer
from thinserve.util import not_implemented


class Session (object):
    def __init__(self, rootobj):
        self._rootobj = rootobj
        self._outq = None
        self._pendingd = None

    def gather_outgoing_messages(self):
        if self._pendingd is None:
            d = defer.Deferred()
            if self._outq is None:
                self._pendingd = d
            else:
                d.callback(self._outq)
                self._outq = None
            return d
        else:
            assert self._outq is None, repr(self._outq)
            # The new request bumps the old one, which fires empty:
            self._pendingq.callback([])
            self._pendingq = defer.Deferred()
            return self._pendingq

    def receive_message(self, msg):
        msg.apply_variant_struct(**self._receivers)

    _receivers = FunctionTableProperty('_')

    @_receivers.register
    def _call(self, id, target, method, params):
        obj = self._resolve_sref(target)
        raise NotImplementedError((id, target, method, params, obj))

    @_receivers.register
    def _reply(self, id, result):
        raise NotImplementedError((id, result))

    @not_implemented
    def _send_call(self, callid, target, method, params):
        pass

    def _resolve_sref(self, sref):
        if sref is None:
            return self._rootobj
        else:
            raise NotImplementedError(sref)
