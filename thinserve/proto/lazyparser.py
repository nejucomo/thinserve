__all__ = ['LazyParser']


import inspect
from types import ClassType, InstanceType, FunctionType, MethodType
from thinserve.proto import error


class LazyParser (object):
    def __init__(self, msg, _path=''):
        self._m = msg
        self._path = _path

    def __repr__(self):
        return '<{} {!r}>'.format(type(self).__name__, self._m)

    def unwrap(self):
        return self._m

    def parse_predicate(self, p):
        desc = p.__doc__
        assert desc is not None, repr(p)
        return self._parse_predicate(
            p,
            error.FailedPredicate,
            {'description': p.__doc__})

    def parse_type(self, t):
        return self._parse_predicate(
            lambda v: isinstance(v, t),
            error.UnexpectedType,
            {'actual': type(self._m).__name__,
             'expected': t.__name__})

    def iter(self):
        l = self.parse_type(list)

        def g():
            for i, x in enumerate(l):
                yield LazyParser(x, '{}[{}]'.format(self._path, i))

        return g()

    def apply_struct(self, f):
        params = dict(
            (k, LazyParser(v, '{}.{}'.format(self._path, k)))
            for (k, v)
            in self.parse_type(dict).iteritems()
        )

        argnames, haskw, dc = get_arg_info(f)
        check_for_missing_or_unknown(
            argnames, params.keys(), haskw, dc, self._path)

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
        [tag, body] = self._parse_predicate(
            lambda v: (isinstance(v, list) and
                       len(v) == 2 and
                       v[0] in fs),
            error.MalformedVariant, {})

        f = fs[tag]
        return f(LazyParser(body, '{}/{}'.format(self._path, tag)))

    # Private:
    def _parse_predicate(self, p, errcls, params):
        if p(self._m):
            return self._m
        else:
            raise errcls(self._path, **params)


def get_arg_info(f):
    assert callable(f), repr(f)

    if type(f) is FunctionType:
        protectfirst = False
    elif type(f) is MethodType:
        protectfirst = True
    elif type(f) in (type, ClassType):
        # It's a class:
        protectfirst = True
        if getattr(f, '__new__', object.__new__) is not object.__new__:
            f = f.__new__
        else:
            f = f.__init__
    elif isinstance(type(f), type) or type(f) is InstanceType:
        # It's a new-style class instance:
        protectfirst = True
        f = f.__call__
    else:
        assert False, 'Unsupported callable: {!r}'.format(f)

    argnames, _, keywords, defaults = inspect.getargspec(f)
    # assertion: varargs is always ignored and unreachable from
    # remote attackers.

    if protectfirst:
        # Protect self/cls parameters:
        argnames.pop(0)

    haskeywords = keywords is not None
    defcount = 0 if defaults is None else len(defaults)

    return argnames, haskeywords, defcount


def check_for_missing_or_unknown(argnames, paramnames, haskw, defcount, path):
    if defcount == 0:
        required = set(argnames)
    else:
        required = set(argnames[:-defcount])

    actual = set(paramnames)

    missing = required - actual
    if missing:
        raise error.MissingStructKeys(path, keys=list(missing))

    if not haskw:
        unknown = actual - set(argnames)
        if unknown:
            raise error.UnexpectedStructKeys(path, keys=list(unknown))
