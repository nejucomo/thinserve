from twisted import internet
from twisted.internet import endpoints
from twisted.web import server
from thinserve.api import resource


class ThinSite (server.Site):
    displayTracebacks = False

    def __init__(self, apiroot, staticdir):
        server.Site.__init__(self, resource.ThinResource(apiroot, staticdir))

    def listen(self, port):
        ep = endpoints.serverFromString(
            internet.reactor,
            'tcp:{}'.format(port))
        ep.listen(self)
