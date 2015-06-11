from thinserve.util import not_implemented


class Session (object):
    def __init__(self, rootobj):
        self._rootobj = rootobj

    @not_implemented
    def gather_outgoing_messages(self):
        pass

    @not_implemented
    def receive_message(self, msg):
        pass

    @not_implemented
    def _send_call(self, callid, target, method, params):
        pass
