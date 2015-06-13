from unittest import TestCase
from thinserve.proto.lazyparser import LazyParser
from thinserve.proto.error import MalformedMessage


class LazyParserPredicateTests (TestCase):
    def test_pos_parse_predicate(self):
        lp = LazyParser(3)

        r = lp.parse_predicate(lambda x: x % 2 == 1)
        self.assertEqual(3, r)

    def test_neg_parse_predicate(self):
        lp = LazyParser(3)

        self.assertRaises(
            MalformedMessage,
            lp.parse_predicate,
            lambda x: x % 2 == 0)

    def test_pos_parse_type(self):
        lp = LazyParser(3)

        r = lp.parse_type(int)
        self.assertEqual(3, r)

    def test_neg_parse_type(self):
        lp = LazyParser(3)

        self.assertRaises(
            MalformedMessage,
            lp.parse_type,
            str)


class LazyParserIterTests (TestCase):
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
            MalformedMessage,
            lp.iter)


class LazyParserStructTests (TestCase):
    def test_pos_apply_struct(self):
        lp = LazyParser({'x': 42, 'y': 17})

        sentinel = object()

        def check(x, y):
            self.assertIsInstance(x, LazyParser)
            self.assertIsInstance(y, LazyParser)
            return sentinel

        r = lp.apply_struct(check)

        self.assertIs(sentinel, r)

    def test_neg_apply_struct_with_method_protects_self(self):
        lp = LazyParser({'x': 42, 's': 17})

        class C (object):
            def method(s, x):
                self._fail_if_called()

        self.assertRaises(MalformedMessage, lp.apply_struct, C().method)

    def test_neg_apply_struct_to_class_protects_self(self):
        lp = LazyParser({'x': 42, 's': 17})

        class C (object):
            def __init__(s, x):
                self._fail_if_called()

        self.assertRaises(MalformedMessage, lp.apply_struct, C)

    def test_neg_apply_struct_with_classmethod_protects_class(self):
        lp = LazyParser({'x': 42, 'c': 17})

        class C (object):
            @classmethod
            def clsmethod(c, x):
                self._fail_if_called()

        self.assertRaises(MalformedMessage, lp.apply_struct, C.clsmethod)
        self.assertRaises(MalformedMessage, lp.apply_struct, C().clsmethod)

    def test_new_apply_struct_with_to_class_protects_new_cls(self):
        lp = LazyParser({'x': 42, 'c': 17})

        class C (object):
            def __new__(c, x):
                self._fail_if_called()

        self.assertRaises(MalformedMessage, lp.apply_struct, C)

    def test_neg_apply_struct_wrong_type(self):
        lp = LazyParser(3)

        self.assertRaises(
            MalformedMessage,
            lp.apply_struct,
            self._fail_if_called)

    def test_neg_apply_struct_missing_expected_keys(self):
        lp = LazyParser({'x': 42})

        def check(x, y):
            self._fail_if_called()

        self.assertRaises(
            MalformedMessage,
            lp.apply_struct,
            check)

    def test_neg_apply_struct_unexpected_keys(self):
        lp = LazyParser({'x': 42, 'y': 17, 'z': 13})

        def check(x, y):
            self._fail_if_called()

        self.assertRaises(
            MalformedMessage,
            lp.apply_struct,
            check)

    def _fail_if_called(self):
        self.fail('Application function called invalidly.')


class LazyParserVariantTests (TestCase):
    def test_pos_apply_variant(self):
        # Setup:
        lp = LazyParser(['animal', {'kind': 'gnome'}])

        sentinel = object()

        def check(kind):
            self.assertIsInstance(kind, LazyParser)
            return sentinel

        r = lp.apply_variant(animal=check)

        self.assertIs(sentinel, r)
