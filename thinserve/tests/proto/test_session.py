from twisted.internet import defer
from twisted.trial.unittest import TestCase
from thinserve.api.referenceable import Referenceable
from thinserve.api.remerr import RemoteError
from thinserve.proto import session
from thinserve.proto.lazyparser import LazyParser
from thinserve.tests.testutil import check_lists_equal


class SessionTests (TestCase):
    def setUp(self):

        self._eaf_info = None

        @Referenceable
        class C (object):
            @Referenceable.Method
            def eat_a_fruit(s, fruit):
                realfruit = fruit.parse_type(str)

                # Note: self is outer self (a SessionTests instance):
                self.assertIsNotNone(self._eaf_info)
                (param, ret) = self._eaf_info
                self._eaf_info = None

                self.assertEqual(param, realfruit)
                return ret

            @Referenceable.Method
            def throw_a_fruit(s, fruit):
                fruit.parse_type(int)

        self.root = C()
        self.s = session.Session(self.root)

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

        # The deferred should be waiting to fire:
        self.failIf(d.called)

        # Do not return d, which will never fire.

    def test_receive_n_immediate_calls_then_gather_n_data_replies(self):
        return self._receive_n_calls_check_replies(
            'eat_a_fruit',
            [
                ['reply',
                 {'id': callid,
                  'result': ['data', reply]}]

                for callid, reply
                in enumerate(self.replies)
            ])

    def test_receive_n_immediate_calls_then_gather_n_error_replies(self):
        tmpl = 'unexpected type {actual}, expecting {expected}'

        return self._receive_n_calls_check_replies(
            'throw_a_fruit',
            [
                ['reply',
                 {'id': i,
                  'result': ['error',
                             {'template': tmpl,
                              'params': {'expected': 'int',
                                         'actual': 'str'},
                              'path': '/call.method/throw_a_fruit.fruit',
                              'message': 'Fruit #{}'.format(i)}]}]

                for i
                in range(len(self.params))
            ])

    def _receive_n_calls_check_replies(self, methodname, expectedreplies):

        callpairs = zip(self.params, self.replies)

        for callid, (param, reply) in enumerate(callpairs):
            self._eaf_info = (param, reply)
            self.s.receive_message(
                LazyParser(
                    ['call',
                     {'id': callid,
                      'target': None,
                      'method': [methodname, {'fruit': param}]}]))

        d = self.s.gather_outgoing_messages()

        # The deferred is called with a reply:
        self.failUnless(d.called)
        d.addCallback(
            lambda msgs: check_lists_equal(self, expectedreplies, msgs))
        return d

    def test_gather_n_calls_then_receive_n_data_replies(self):
        return self._gather_n_calls_then_receive_replies(
            'eat_a_fruit',
            make_result=lambda reply: ['data', reply],
            check_result=lambda res, reply: self.assertIs(reply, res.unwrap()),
            check_err=None)

    def test_gather_n_calls_then_receive_n_error_replies(self):
        return self._gather_n_calls_then_receive_replies(
            'eat_a_fruit',
            make_result=lambda reply: ['error', reply],
            check_result=lambda _x, _y: self.fail('Unexpected'),
            check_err=lambda f: self.assertIsInstance(f.value, RemoteError))

    def _gather_n_calls_then_receive_replies(self,
                                             methodname,
                                             make_result,
                                             check_result,
                                             check_err):
        fakeid = 'fake-client-id'

        repdefs = []

        # Prime the (private) outgoing call queue:
        for param in self.params:
            repdefs.append(
                self.s._send_call(
                    target=fakeid,
                    method=methodname,
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
                      'method': [methodname, {'fruit': param}]}]

                    for callid, param
                    in enumerate(self.params)
                ],
                messages)

            for callid, (reply, d) in enumerate(zip(self.replies, repdefs)):
                self.failIf(d.called)

                self.s.receive_message(
                    LazyParser(
                        ['reply',
                         {'id': callid,
                          'result': make_result(reply)}]))

                self.failUnless(d.called)
                d.addCallbacks(check_result, check_err, callbackArgs=(reply,))

        # Note: d is done here, we can forget it.
        return defer.DeferredList(repdefs)
