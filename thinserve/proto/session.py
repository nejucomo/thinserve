from twisted.internet import defer
from thinserve.util import not_implemented
from thinserve.proto import error


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
        try:
            [action, detail] = msg
        except ValueError:
            raise error.MalformedMessage()

        if action == 'call':
            return self._receive_call(detail)
        elif action == 'reply':
            return self._receive_reply(detail)
        else:
            raise error.MalformedMessage()

    @not_implemented
    def _send_call(self, callid, target, method, params):
        pass

    @not_implemented
    def _receive_call(self, detail):
        pass

    @not_implemented
    def _receive_reply(self, detail):
        pass
