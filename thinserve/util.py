from functools import wraps


def not_implemented(f):
    @wraps(f)
    def g(*a, **kw):
        # Call it first, in case it has a partial implementation:
        f(*a, **kw)
        raise NotImplemented((f, a, kw))
    return g
