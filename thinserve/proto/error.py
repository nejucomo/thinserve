from proptools import SetOnceProperty


class ProtocolError (Exception):
    # Subclasses should define Template as a class property.

    params = SetOnceProperty()

    def __init__(self, **kw):
        Exception.__init__(self, self.Template.format(**kw))
        self.params = kw

    def as_proto_object(self):
        return {
            'template': self.Template,
            'params': self.params,
            }


class InternalError (ProtocolError):
    Template = 'internal error'

    @staticmethod
    def coerce_unexpected_failure(f):
        '''Log unexpected exceptions and coerce into InternalError.'''
        if isinstance(f.value, ProtocolError):
            return f
        else:
            f.printTraceback()
            raise InternalError()


class UnsupportedHTTPMethod (ProtocolError):
    Template = 'unsupported HTTP method "{method}"'


class UnexpectedHTTPBody (ProtocolError):
    Template = 'unexpected HTTP body'


class MalformedJSON (ProtocolError):
    Template = 'malformed JSON'


class MalformedMessage (ProtocolError):
    def __init__(self, path, **params):
        ProtocolError.__init__(self, **params)
        self.path = path

    def as_proto_object(self):
        return {
            'template': self.Template,
            'params': self.params,
            'path': self.path,
            }


class UnexpectedType (MalformedMessage):
    Template = 'expected type {actual}, expecting {expected}'


class FailedPredicate (MalformedMessage):
    Template = 'failed predicate: {description}'


class MalformedVariant (MalformedMessage):
    Template = 'expected variant [<tag>, <value>]'


class UnexpectedStructKeys (MalformedMessage):
    Template = 'unexpected struct keys {keys}'


class MissingStructKeys (MalformedMessage):
    Template = 'missing struct keys {keys}'


class InvalidParameter (ProtocolError):
    Template = 'invalid parameter "{name}"'
