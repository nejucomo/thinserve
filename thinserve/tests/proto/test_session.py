from unittest import TestCase
from mock import MagicMock, call, sentinel
from thinserve.proto import session
from thinserve.tests.testutil import check_mock, check_lists_equal


class SessionTests (TestCase):
    def setUp(self):
        self.m_root = MagicMock(name='createsession')
        self.s = session.Session(self.m_root)

    def test_empty_gather_outgoing_messages(self):
        d = self.s.gather_outgoing_messages()

        check_mock(
            self, self.m_root,
            [])

        # The deferred should be waiting to fire:
        self.failIf(d.called)

    def test_receive_call_then_gather_one_message(self):
        self.m_root.eat_a_fruit.return_value = 'Yum!'
        self.s.receive_message(
            ['call',
             {'id': sentinel.callid,
              'target': None,
              'method': 'eat_a_fruit',
              'params': {'fruit': 'apple'}}])

        d = self.s.gather_outgoing_messages()

        check_mock(
            self, self.m_root,
            [call.eat_a_fruit(fruit='apple')])

        # The deferred be called with a reply:
        self.failUnless(d.called)

        @d.addCallback
        def take_messages(replies):
            check_lists_equal(
                self,
                [['reply',
                  {'id': sentinel.callid,
                   'result': ['data', 'Yum!']}]],
                replies)
