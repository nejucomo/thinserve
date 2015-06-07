import os
from unittest import TestCase
from mock import call, patch, sentinel
from thinserve.api.resource import ThinResource


class ThinResourceTests (TestCase):
    @patch('thinserve.api.apiresource.ThinAPIResource')
    @patch('thinserve.api.resource.ThinResource.putChild')
    @patch('twisted.web.static.File')
    @patch('pkg_resources.resource_filename')
    @patch('os.listdir')
    def test__init__(self,
                     m_listdir,
                     m_resource_filename,
                     m_File,
                     m_putChild,
                     m_ThinAPIResource):

        staticdir = os.path.join('fake', 'test', 'staticdir')
        childnames = ['child'+str(i) for i in range(7)]
        childpaths = [os.path.join(staticdir, cn) for cn in childnames]

        m_listdir.return_value = childnames
        ThinResource(sentinel.apiroot, staticdir)

        self.assertEqual(
            m_putChild.mock_calls,
            [call('api', m_ThinAPIResource.return_value),
             call('ts', m_File.return_value)]
            + [call(cn, m_File.return_value) for cn in childnames])

        self.assertEqual(
            m_ThinAPIResource.mock_calls,
            [call(sentinel.apiroot)])

        self.assertEqual(
            m_resource_filename.mock_calls,
            [call('thinserve', 'web/static')])

        self.assertEqual(
            m_File.mock_calls,
            [call(m_resource_filename.return_value)]
            + [call(p) for p in childpaths])
