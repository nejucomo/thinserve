from unittest import TestCase
from mock import call, patch, sentinel
from thinserve import ThinServer


class ThinServerTests (TestCase):
    def test__init__(self):
        self._test_init()

    @patch('twisted.internet.endpoints.serverFromString')
    @patch('twisted.internet.reactor')
    def test_listen(self, m_reactor, m_serverFromString):
        ts = self._test_init()
        ts.listen(port=4242)

        self.assertEqual(
            m_serverFromString.mock_calls,
            [call(m_reactor, 'tcp:4242'),
             call().listen(ts._site)])

    @patch('thinserve.resource.ThinResource')
    @patch('twisted.web.server.Site')
    def _test_init(self, m_Site, m_ThinResource):
        ts = ThinServer(sentinel.apiroot, sentinel.staticdir)

        self.assertEqual(ts._site.displayTracebacks, False)

        self.assertEqual(
            m_ThinResource.mock_calls,
            [call(sentinel.apiroot, sentinel.staticdir)])

        self.assertEqual(
            m_Site.mock_calls,
            [call(m_ThinResource.return_value)])

        return ts
