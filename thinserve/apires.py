from twisted.web import resource


class APIResource (resource.Resource):
    def __init__(self, apiroot):
        self._apiroot = apiroot
        resource.Resource.__init__(self)
