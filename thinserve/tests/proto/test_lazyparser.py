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


class _FailIfCalledBase (TestCase):
    def _fail_if_called(self):
        self.fail('Application function called invalidly.')


class LazyParser_struct (_FailIfCalledBase):
    def test_pos_apply_struct(self):
        lp = LazyParser({'x': 42, 'y': 17})

        sentinel = object()

        def check(x, y):
            self.assertIsInstance(x, LazyParser)
            self.assertIsInstance(y, LazyParser)
            return sentinel

        r = lp.apply_struct(check)

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


class LazyParser_struct_protected_privileged_parameter (_FailIfCalledBase):
    def test_neg_apply_struct_to_instance_method(self):
        lp = LazyParser({'x': 42, 's': 17})

        class C (object):
            def method(s, x):
                self._fail_if_called()

        self.assertRaises(
            error.UnexpectedStructKeys,
            lp.apply_struct,
            C().method)

    def test_neg_apply_struct_to__init__(self):
        lp = LazyParser({'x': 42, 's': 17})

        class C (object):
            def __init__(s, x):
                self._fail_if_called()

        self.assertRaises(
            error.UnexpectedStructKeys,
            lp.apply_struct,
            C)

    def test_neg_apply_struct_to_classmethod(self):
        lp = LazyParser({'x': 42, 'c': 17})

        class C (object):
            @classmethod
            def clsmethod(c, x):
                self._fail_if_called()

        for m in [C.clsmethod, C().clsmethod]:
            self.assertRaises(
                error.UnexpectedStructKeys,
                lp.apply_struct,
                C.clsmethod)

    def test_new_apply_struct_to__new__(self):
        lp = LazyParser({'x': 42, 'c': 17})

        class C (object):
            def __new__(c, x):
                self._fail_if_called()

        self.assertRaises(
            error.UnexpectedStructKeys,
            lp.apply_struct,
            C)


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
