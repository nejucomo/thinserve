__all__ = ['LazyParser']


import re
import inspect
from types import ClassType, InstanceType, FunctionType, MethodType
from thinserve.proto import error


_IdentifierRgx = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')


class LazyParser (object):
    def __init__(self, msg, _path=''):
        self._m = msg
        self._path = _path

    def __repr__(self):
        return '<{} {!r}>'.format(type(self).__name__, self._m)

    def unwrap(self):
        v = self._peel()
        if isinstance(v, list):
            return [lp.unwrap() for lp in v]
        elif isinstance(v, tuple):
            (tag, lp) = v
            return (tag, lp.unwrap())
        elif isinstance(v, dict):
            return dict(
                (k, lp.unwrap())
                for (k, lp)
                in v.iteritems()
                )
        else:
            return v

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
            {
                'actual': type(self._m).__name__,
                'expected': t.__name__,
            })

    def iter(self):
        return iter(self.parse_type(list))

    def apply_struct(self, f):
        params = self.parse_type(dict)
        self._check_arg_info(f, params.keys())
        return f(**params)

    def apply_variant_struct(self, **fs):
        return self.apply_variant(
            **dict(
                (k,
                 lambda lp, f=f: lp.apply_struct(f))

                for (k, f)
                in fs.iteritems()
            )
        )

    def apply_variant(self, **fs):
        (tag, body) = self.parse_type(tuple)

        try:
            f = fs[tag]
        except KeyError:
            raise error.UnknownVariantTag(
                self._path,
                self._m,
                tag=tag,
                knowntags=sorted(fs.keys()))

        return f(body)

    # Private:
    def _peel(self):
        def sublp(v, tmpl, key):
            return LazyParser(
                v,
                ('{}' + tmpl).format(self._path, key))

        v = self._m

        if isinstance(v, list):
            if v == []:
                return []
            elif v[0] == '@LIST':
                return [
                    sublp(x, '[{}]', i)
                    for i, x in enumerate(v[1:])
                ]
            else:
                try:
                    [tag, value] = v
                except ValueError:
                    raise error.MalformedList(self._path, v)

                self._verify_identifier(tag)
                return (tag, sublp(value, '/{}', tag))

        elif isinstance(v, dict):
            return dict(
                (self._verify_identifier(k),
                 sublp(v, '.{}', k))
                for (k, v) in v.iteritems())

        else:
            return v

    def _parse_predicate(self, p, errcls, params):
        v = self._peel()
        if p(v):
            return v
        else:
            raise errcls(self._path, self._m, **params)

    def _check_arg_info(self, f, paramnames):
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

        defcount = 0 if defaults is None else len(defaults)

        if defcount == 0:
            required = set(argnames)
        else:
            required = set(argnames[:-defcount])

        actual = set(paramnames)

        missing = required - actual
        if missing:
            raise error.MissingStructKeys(
                self._path, self._m, keys=list(missing))

        if keywords is None:
            unknown = actual - set(argnames)
            if unknown:
                raise error.UnexpectedStructKeys(
                    self._path, self._m, keys=list(unknown))

    def _verify_identifier(self, ident):
        if _IdentifierRgx.match(ident):
            return ident
        else:
            raise error.InvalidIdentifier(
                self._path,
                self._m,
                ident=ident)
