from functools import wraps


def not_implemented(f):
    @wraps(f)
    def g(*a, **kw):
        # Call it first, in case it has a partial implementation:
        f(*a, **kw)
        raise NotImplementedError((f, a, kw))
    return g


def Singleton(C):
    """A class decorator for singleton classes."""
    return C()
