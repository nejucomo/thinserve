"""
Mark classes and their methods as accessible to the remote side.
"""

__all__ = ['Referenceable']


from types import MethodType
from weakref import WeakKeyDictionary
from thinserve.util import Singleton


@Singleton
class Referenceable (object):
    """I am a class and method decorator for referenceable types."""
    def __init__(self):
        self._classes = {}
        self._instances = WeakKeyDictionary()
        self._methodcache = {}

    # Application Interface:
    def __call__(self, cls):
        """Decorate a class; without this, it cannot be remotely referenced."""
        methodinfo = {}

        for v in vars(cls).itervalues():
            try:
                remotename = self._methodcache[v]
            except KeyError:
                # It's not remotely accessible:
                pass
            else:
                methodinfo[remotename] = v

        self._classes[cls] = methodinfo
        self._methodcache.clear()
        return cls

    def Method(self, f):
        """Decorate a method; the class must be decorated."""
        return self._register_method(f, f.__name__)

    def Method_without_prefix(self, prefix):
        """Decorate a method, but drop prefix from the remote name."""
        def decorator(f):
            assert f.__name__.startswith(prefix), (f, prefix)
            return self._register_method(f, f.__name__[len(prefix):])
        return decorator

    # Framework interface (private to apps):
    def _check(self, obj):
        return type(obj) in self._classes

    def _get_bound_methods(self, obj):
        cls = type(obj)
        try:
            return self._instances[obj]
        except KeyError:
            boundmethods = dict(
                (name, MethodType(m, obj, cls))
                for (name, m)
                in self._classes[cls].iteritems()
            )
            self._instances[obj] = boundmethods
            return boundmethods

    # Class Private:
    def _register_method(self, f, name):
        self._methodcache[f] = name
        return f
