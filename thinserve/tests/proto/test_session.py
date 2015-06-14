from unittest import TestCase
from mock import MagicMock, call
from thinserve.proto import session
from thinserve.proto.lazyparser import LazyParser
from thinserve.tests.testutil import check_mock, check_lists_equal


class SessionTests (TestCase):
    def setUp(self):
        self.m_root = MagicMock(name='createsession')
        self.s = session.Session(self.m_root)

        # Setup some immediate call/reply info:
        self.replies = []
        self.params = []

        setupinfo = [('Yum {}!', self.replies),
                     ('Fruit #{}', self.params)]
        for i in range(17):
            for tmpl, container in setupinfo:
                container.append(tmpl.format(i))

    def test_empty_gather_outgoing_messages(self):
        d = self.s.gather_outgoing_messages()

        check_mock(
            self, self.m_root,
            [])

        # The deferred should be waiting to fire:
        self.failIf(d.called)

    def test_receive_n_immediate_calls_then_gather_n_replies(self):
        self.m_root.eat_a_fruit.side_effect = self.replies

        for callid, param in enumerate(self.params):
            self.s.receive_message(
                LazyParser(
                    ['call',
                     {'id': callid,
                      'target': None,
                      'method': 'eat_a_fruit',
                      'params': {'fruit': param}}]))

        d = self.s.gather_outgoing_messages()

        check_mock(
            self, self.m_root,
            [call.eat_a_fruit(fruit=p) for p in self.params])

        # The deferred be called with a reply:
        self.failUnless(d.called)

        @d.addCallback
        def take_messages(messages):
            check_lists_equal(
                self,
                [
                    ['reply',
                     {'id': callid,
                      'result': ['data', reply]}]

                    for callid, reply
                    in enumerate(self.replies)
                ],
                messages)

    def test_gather_n_calls_then_receive_n_replies(self):
        fakeid = 'fake-client-id'

        repdefs = []

        # Prime the (private) outgoing call queue:
        for callid, param in enumerate(self.params):
            repdefs.append(
                self.s._send_call(
                    callid=callid,
                    target=fakeid,
                    method='eat_a_fruit',
                    params={'fruit': param}))

        d = self.s.gather_outgoing_messages()

        self.failUnless(d.called)

        @d.addCallback
        def take_messages(messages):
            check_lists_equal(
                self,
                [
                    ['call',
                     {'id': callid,
                      'target': fakeid,
                      'method': 'eat_a_fruit',
                      'params': {'fruit': param}}]

                    for callid, reply
                    in enumerate(self.params)
                ],
                messages)

            for callid, (reply, d) in enumerate(zip(self.replies, repdefs)):
                self.failIf(d.called)

                self.s.receive_message(
                    LazyParser(
                        ['reply',
                         {'id': callid,
                          'result': ['data', reply]}]))

                self.failUnless(d.called)

                d.addCallback(lambda res: self.assertIs(res, reply))
