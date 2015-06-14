from unittest import TestCase
from thinserve.proto.lazyparser import LazyParser
from thinserve.proto import error


class LazyParser_basic (TestCase):
    def test_repr(self):
        lp = LazyParser({'x': 42})
        self.assertEqual("<LazyParser {'x': 42}>", repr(lp))

    def test_unwrap(self):
        sentinel = object()
        lp = LazyParser(sentinel)
        self.assertIs(sentinel, lp.unwrap())


class LazyParser_type_and_predicate (TestCase):
    def test_neg_parse_predicate(self):
        lp = LazyParser(3)

        self.assertRaises(
            error.MalformedMessage,
            lp.parse_predicate,
            lambda x: x % 2 == 0)

    def test_pos_parse_type(self):
        lp = LazyParser(3)

        r = lp.parse_type(int)
        self.assertEqual(3, r)

    def test_neg_parse_type(self):
        lp = LazyParser(3)

        self.assertRaises(
            error.MalformedMessage,
            lp.parse_type,
            str)


class LazyParser_iter (TestCase):
    def test_pos_iter(self):
        lp = LazyParser([1, 2, 3])

        c = 0
        for sublp in lp.iter():
            c += 1
            self.assertIsInstance(sublp, LazyParser)
        self.assertEqual(3, c)

    def test_neg_iter(self):
        lp = LazyParser(3)

        self.assertRaises(
            error.MalformedMessage,
            lp.iter)


class LazyParser_struct (TestCase):
    def test_pos_apply_struct(self):
        lp = LazyParser({'x': 42, 'y': 17})

        sentinel = object()

        def check(x, y):
            self.assertIsInstance(x, LazyParser)
            self.assertIsInstance(y, LazyParser)
            return sentinel

        r = lp.apply_struct(check)

        self.assertIs(sentinel, r)

    def test_pos_apply_struct_varargs_ignored(self):
        lp = LazyParser({'x': 42, 'y': 17})

        sentinel = object()

        def check(x, y, *a):
            self.assertIsInstance(x, LazyParser)
            self.assertIsInstance(y, LazyParser)
            self.assertIs(a, ())
            return sentinel

        r = lp.apply_struct(check)

        self.assertIs(sentinel, r)

    def test_pos_apply_struct_kwargs_accept_extra_keys(self):
        lp = LazyParser({'x': 42, 'y': 17})

        sentinel = object()

        def check(x, **kw):
            self.assertIsInstance(x, LazyParser)
            self.assertEqual(['y'], kw.keys())
            self.assertIsInstance(kw['y'], LazyParser)
            return sentinel

        r = lp.apply_struct(check)

        self.assertIs(sentinel, r)

    def test_pos_apply_struct_with_defaults(self):
        lp1 = LazyParser({'x': 42, 'y': 17})
        lp2 = LazyParser({'x': 42, 'y': 17, 'z': 'banana'})

        sentinel = object()

        def check(x, y, z=LazyParser('blah')):
            self.assertIsInstance(x, LazyParser)
            self.assertIsInstance(y, LazyParser)
            self.assertIsInstance(z, LazyParser)
            return sentinel

        r = lp1.apply_struct(check)
        self.assertIs(sentinel, r)

        r = lp2.apply_struct(check)
        self.assertIs(sentinel, r)

    def test_neg_apply_struct_wrong_type(self):
        lp = LazyParser(3)

        self.assertRaises(
            error.MalformedMessage,
            lp.apply_struct,
            self._fail_if_called)

    def test_neg_apply_struct_missing_expected_keys(self):
        lp = LazyParser({'x': 42})

        def check(x, y):
            self._fail_if_called()

        self.assertRaises(
            error.MissingStructKeys,
            lp.apply_struct,
            check)

    def test_neg_apply_struct_unexpected_keys(self):
        lp = LazyParser({'x': 42, 'y': 17, 'z': 13})

        def check(x, y):
            self._fail_if_called()

        self.assertRaises(
            error.UnexpectedStructKeys,
            lp.apply_struct,
            check)

    # Helper code:
    def _fail_if_called(self):
        self.fail('Application function called invalidly.')


class LazyParser_struct_protected_privileged_parameter (TestCase):
    def test_apply_struct_to__init__(self):
        class C (object):
            def __init__(protected, x):
                pass

        self._check(C)

    def test_apply_struct_to__new__(self):
        class C (object):
            def __new__(protected, x):
                pass

        self._check(C)

    def test_apply_struct_to__call__(self):
        class C (object):
            def __call__(protected, x):
                pass

        self._check(C())

    def test_apply_struct_to_instance_method(self):
        class C (object):
            def method(protected, x):
                pass

        self._check(C().method)

    def test_apply_struct_to_classmethod(self):
        class C (object):
            @classmethod
            def clsmethod(protected, x):
                pass

        self._check(C.clsmethod)
        self._check(C().clsmethod)

    def test_apply_struct_to__init__old_style(self):
        class C:
            def __init__(protected, x):
                pass

        self._check(C)

    def test_apply_struct_to__call__old_style(self):
        class C:
            def __call__(protected, x):
                pass

        self._check(C())

    def test_apply_struct_to_instance_method_old_style(self):
        class C:
            def method(protected, x):
                pass

        self._check(C().method)

    def test_apply_struct_to_classmethod_old_style(self):
        class C:
            @classmethod
            def clsmethod(protected, x):
                pass

        self._check(C.clsmethod)
        self._check(C().clsmethod)

    # Helper code:
    def _check(self, f):
        self._check_pos(f)
        self._check_neg(f)

    def _check_pos(self, f):
        lp = LazyParser({'x': 42})
        lp.apply_struct(f)

    def _check_neg(self, f):
        lp = LazyParser(
            {'protected': 'malicious input',
             'x': 42})

        self.assertRaises(
            error.UnexpectedStructKeys,
            lp.apply_struct,
            f)


class LazyParser_variant (TestCase):
    def test_pos_apply_variant_struct(self):
        # Setup:
        lp = LazyParser(['animal', {'kind': 'gnome', 'name': 'bob'}])

        sentinel = object()

        def check(kind, name):
            self.assertIsInstance(kind, LazyParser)
            self.assertIsInstance(name, LazyParser)
            return sentinel

        r = lp.apply_variant_struct(animal=check)

        self.assertIs(sentinel, r)

    def test_pos_apply_variant(self):
        # Setup:
        lp = LazyParser(['animal', {'kind': 'gnome', 'name': 'bob'}])

        sentinel = object()

        def check(lp):
            self.assertIsInstance(lp, LazyParser)
            return sentinel

        r = lp.apply_variant(animal=check)

        self.assertIs(sentinel, r)
