__all__ = ['LazyParser']


import inspect
from types import MethodType
from thinserve.proto.error import MalformedMessage


class LazyParser (object):
    def __init__(self, msg):
        self._m = msg

    def parse_predicate(self, p):
        if p(self._m):
            return self._m
        else:
            raise MalformedMessage()

    def parse_type(self, t):
        return self.parse_predicate(lambda v: isinstance(v, t))

    def iter(self):
        l = self.parse_type(list)

        def g():
            for x in l:
                yield LazyParser(x)

        return g()

    def apply_struct(self, f):
        params = dict(
            (k, LazyParser(v))
            for (k, v)
            in self.parse_type(dict).iteritems()
        )

        argnames = get_arg_names(f)
        params, argnames = get_mangled_params(type(f), params, argnames)
        check_for_missing_or_unknown(argnames, params.keys())
        return f(**params)

    def apply_variant(self, **fs):
        [tag, body] = self.parse_predicate(
            lambda v: (isinstance(v, list) and
                       len(v) == 2 and
                       v[0] in fs)
            )

        f = fs[tag]
        return LazyParser(body).apply_struct(f)


def get_mangled_params(ftype, params, argnames):
    if ftype is MethodType:
        selfname = argnames.pop(0)

        if selfname in params:
            collidingvalue = params.pop(selfname)
            mangled = selfname + '_'
            while mangled in params:
                mangled += '_'
            params[mangled] = collidingvalue

    return params, argnames


def get_arg_names(f):
    spec = inspect.getargspec(f)
    assert spec.varargs is None, \
        'Invalid struct func {!r} accepts varargs'.format(f)
    assert spec.keywords is None, \
        'Invalid struct func {!r} accepts keywords'.format(f)
    assert spec.defaults is None, \
        'Invalid struct func {!r} accepts defaults'.format(f)

    return spec.args


def check_for_missing_or_unknown(argnames, paramnames):
    required = set(argnames)
    actual = set(paramnames)

    missing = required - actual
    if missing:
        raise MalformedMessage()

    unknown = actual - required
    if unknown:
        raise MalformedMessage()
