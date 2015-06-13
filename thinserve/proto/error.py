from proptools import SetOnceProperty


class ProtocolError (Exception):
    # Subclasses should define Template as a class property.

    params = SetOnceProperty()

    def __init__(self, **kw):
        Exception.__init__(self, self.Template.format(**kw))
        self.params = kw


class InternalError (ProtocolError):
    Template = 'internal error'


class UnsupportedHTTPMethod (ProtocolError):
    Template = 'unsupported HTTP method "{method}"'


class UnexpectedHTTPBody (ProtocolError):
    Template = 'unexpected HTTP body'


class MalformedJSON (ProtocolError):
    Template = 'malformed JSON'


class MalformedMessage (ProtocolError):
    Template = 'malformed message'


class UnexpectedStructKeys (MalformedMessage):
    Template = 'unexpected struct keys "{keys}"'


class MissingStructKeys (MalformedMessage):
    Template = 'missing struct keys "{keys}"'


class InvalidParameter (ProtocolError):
    Template = 'invalid parameter "{name}"'
