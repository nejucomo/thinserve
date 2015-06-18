from functable import FunctionTableProperty


class Shuttle (object):
    '''I hold either pending HTTP response or pending outgoing messages.'''
    def __init__(self):
        self._state = _Empty

    def send_message(self, msg):
        self._apply(self._senders, msg)

    def gather_messages(self, d):
        self._apply(self._gatherers, d)

    # Private:
    def _apply(self, ftab, arg):
        (tag, state) = self._state
        ftab[tag](state, arg)

    _senders = FunctionTableProperty('_send_')

    @_senders.register
    def _send_empty(self, _, msg):
        self._state = ('queued', [msg])

    @_senders.register
    def _send_queued(self, q, msg):
        q.append(msg)

    @_senders.register
    def _send_blocked(self, d, msg):
        d.callback([msg])
        self._state = _Empty

    _gatherers = FunctionTableProperty('_gather_')

    @_gatherers.register
    def _gather_empty(self, _, d):
        self._state = ('blocked', d)

    @_gatherers.register
    def _gather_queued(self, q, d):
        d.callback(q)
        self._state = _Empty

    @_gatherers.register
    def _gather_blocked(self, oldd, newd):
        oldd.callback([])
        self._state = ('blocked', newd)


_Empty = ('empty', None)
