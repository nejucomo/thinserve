from unittest import TestCase
from mock import call, patch, sentinel, ANY
from thinserve.api.site import ThinSite


class ThinSiteTests (TestCase):
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
             call().listen(ts)])

    @patch('thinserve.api.resource.ThinResource')
    @patch('twisted.web.server.Site.__init__')
    def _test_init(self, m_Site__init__, m_ThinResource):
        ts = ThinSite(sentinel.apiroot, sentinel.staticdir)

        self.assertEqual(ts.displayTracebacks, False)

        self.assertEqual(
            m_ThinResource.mock_calls,
            [call(sentinel.apiroot, sentinel.staticdir)])

        self.assertEqual(
            m_Site__init__.mock_calls,
            [call(ANY, m_ThinResource.return_value)])

        return ts
