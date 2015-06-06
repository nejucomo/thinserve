from twisted import internet
from twisted.internet import endpoints
from twisted.web import server
from thinserve import resource


class ThinServer (object):
    def __init__(self, apiroot, staticdir):
        self._site = server.Site(resource.ThinResource(apiroot, staticdir))
        self._site.displayTracebacks = False

    def listen(self, port):
        ep = endpoints.serverFromString(
            internet.reactor,
            'tcp:{}'.format(port))
        ep.listen(self._site)
