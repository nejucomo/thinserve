from unittest import TestCase
from mock import MagicMock, call
from thinserve.proto.shuttle import Shuttle, _Empty
from thinserve.tests.testutil import check_mock


class ShuttleTests (TestCase):
    def setUp(self):
        self.sh = Shuttle()

    def test_empty(self):
        self.assertEqual(self.sh._state, _Empty)

    def test_send(self):
        msg = MagicMock()
        self.sh.send_message(msg)
        self.assertEqual(self.sh._state, ('queued', [msg]))

    def test_gather(self):
        d = MagicMock()
        self.sh.gather_messages(d)
        self.assertEqual(self.sh._state, ('blocked', d))

    def test_send_then_gather(self):
        msg = MagicMock()
        self.sh.send_message(msg)
        d = MagicMock()
        self.sh.gather_messages(d)
        self.assertEqual(self.sh._state, _Empty)
        check_mock(self, d, [call.callback([msg])])

    def test_gather_then_send(self):
        d = MagicMock()
        self.sh.gather_messages(d)
        check_mock(self, d, [])
        msg = MagicMock()
        self.sh.send_message(msg)
        self.assertEqual(self.sh._state, _Empty)
        check_mock(self, d, [call.callback([msg])])

    def test_many_sends(self):
        msgs = [MagicMock(name='message {}'.format(i)) for i in range(17)]
        for msg in msgs:
            self.sh.send_message(msg)

        self.assertEqual(self.sh._state, ('queued', msgs))

    def test_many_gathers(self):
        c = [0]  # A closure.

        def make_mock_deferred():
            d = MagicMock(name='Deferred {}'.format(c[0]))
            c[0] += 1
            return d

        check_not_touched = lambda d: check_mock(self, d, [])

        oldd = make_mock_deferred()
        self.sh.gather_messages(oldd)
        check_not_touched(oldd)

        for i in range(17):
            d = make_mock_deferred()
            self.sh.gather_messages(d)
            check_mock(self, oldd, [call.callback([])])
            oldd = d
