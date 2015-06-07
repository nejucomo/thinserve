import os
import pkg_resources
from twisted.web import resource, static
from thinserve.api import apiresource


class ThinResource (resource.Resource):
    def __init__(self, apiroot, staticdir):
        resource.Resource.__init__(self)

        self.putChild('api', apiresource.ThinAPIResource(apiroot))
        self.putChild(
            'ts',
            static.File(
                pkg_resources.resource_filename('thinserve', 'web/static'),
            ),
        )

        for name in os.listdir(staticdir):
            assert name not in ['api', 'ts'], \
                'Reserved name: {!r}'.format(name)

            childpath = os.path.join(staticdir, name)
            self.putChild(name, static.File(childpath))
