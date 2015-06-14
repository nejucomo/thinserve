__all__ = ['LazyParser']


import inspect
from types import MethodType
from thinserve.proto import error


class LazyParser (object):
    def __init__(self, msg):
        self._m = msg

    def unwrap(self):
        return self._m

    def parse_predicate(self, p):
        if p(self._m):
            return self._m
        else:
            raise error.MalformedMessage()

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
        check_for_missing_or_unknown(argnames, params.keys())
        return f(**params)

    def apply_variant_struct(self, **fs):
        return self.apply_variant(
            **dict(
                (k, lambda lp, f=f: lp.apply_struct(f))
                for (k, f)
                in fs.iteritems()
            )
        )

    def apply_variant(self, **fs):
        [tag, body] = self.parse_predicate(
            lambda v: (isinstance(v, list) and
                       len(v) == 2 and
                       v[0] in fs)
            )

        f = fs[tag]
        return f(LazyParser(body))


def get_arg_names(f):
    protectfirst = False

    if type(f) is type:
        protectfirst = True
        if f.__new__ is not object.__new__:
            f = f.__new__
        else:
            f = f.__init__
    elif type(f) is MethodType:
        protectfirst = True

    spec = inspect.getargspec(f)
    assert spec.varargs is None, \
        'Invalid struct func {!r} accepts varargs'.format(f)
    assert spec.keywords is None, \
        'Invalid struct func {!r} accepts keywords'.format(f)
    assert spec.defaults is None, \
        'Invalid struct func {!r} accepts defaults'.format(f)

    if protectfirst:
        # Protect self/cls parameters:
        return spec.args[1:]
    else:
        return spec.args


def check_for_missing_or_unknown(argnames, paramnames):
    required = set(argnames)
    actual = set(paramnames)

    missing = required - actual
    if missing:
        raise error.MissingStructKeys(keys=list(missing))

    unknown = actual - required
    if unknown:
        raise error.UnexpectedStructKeys(keys=list(unknown))
