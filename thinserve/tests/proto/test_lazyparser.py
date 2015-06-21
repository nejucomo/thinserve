from unittest import TestCase
from thinserve.proto.lazyparser import LazyParser
from thinserve.proto import error


InvalidIdentifiers = [
    '',
    '_leading_underscores_disallowed',
    '@sign_reserved_for_protocol_tags',
    'has a space',
    'weird^char',
    'another-unacceptable-char',
    '1s_digit_initial',
]


class LazyParser_basic (TestCase):
    def test_repr(self):
        lp = LazyParser({'x': 42})
        self.assertEqual("<LazyParser {'x': 42}>", repr(lp))


class LazyParser_unwrap (TestCase):
    # These cases unwrap to equal values:
    _eq_cases = [
        None, False, True,
        0, -1, 42,
        [], {},
        {'x': 42},
        ]

    # These cases map left to right when parsing:
    _uneq_cases = [
        (['@LIST'], []),
        (['my_variant', 42], ('my_variant', 42)),

        # Test all three kinds of recursion:
        (['my_variant', ['@LIST', {'x': ['@LIST']}]],
         ('my_variant', [{'x': []}])),
        ]

    _error_cases = [
        ['foo'],  # Ambiguous: List or variant?
        ]

    def test_pos_unwrap_eq_values(self):
        for msg in self._eq_cases:
            lp = LazyParser(msg)
            self.assertEqual(msg, lp.unwrap())

    def test_pos_unwrap_uneq_values(self):
        for msg, expected in self._eq_cases:
            lp = LazyParser(msg)
            self.assertEqual(expected, lp.unwrap())

    def test_neg_unwrap(self):
        for badmsg in self._error_cases:
            lp = LazyParser(badmsg)
            self.assertRaises(error.MalformedMessage, lp.unwrap)


class LazyParser_type_and_predicate (TestCase):
    def test_neg_parse_predicate(self):
        lp = LazyParser(3)

        def is_even(x):
            '''it is an even value'''
            return x % 2 == 0

        self.assertRaises(error.FailedPredicate, lp.parse_predicate, is_even)

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


class LazyParser_list (TestCase):
    def setUp(self):
        lists = [
            [0, 1, 2],
            ['x', 'y', 'z'],
            ]

        posmsgs = [
            [],
            ['@LIST'],
        ] + [
            ['@LIST'] + x
            for x in lists
        ]

        self.poslps = [
            (m[1:], LazyParser(m))
            for m in posmsgs
        ]

        self.neglps = [LazyParser(x) for x in lists]

    def test_pos_parse_list(self):
        for x, lp in self.poslps:
            self.assertEqual(x, lp.parse_type(list))

    def test_pos_unwrap(self):
        for x, lp in self.poslps:
            self.assertEqual(x, lp.unwrap())

    def test_neg_parse_list(self):
        for lp in self.neglps:
            self.assertRaises(error.MalformedList, lp.parse_type, list)

    def test_neg_unwrap(self):
        for lp in self.neglps:
            self.assertRaises(error.MalformedList, lp.unwrap)

    def test_pos_iter(self):
        for x, lp in self.poslps:
            c = 0
            for (elem, sublp) in zip(x, lp.iter()):
                c += 1
                self.assertIsInstance(sublp, LazyParser)
                self.assertIs(elem, sublp.unwrap())

            self.assertEqual(len(x), c)

    def test_neg_iter(self):
        for _, lp in self.neglps:
            self.assertRaises(error.MalformedList, lp.iter)

    def test_neg_non_array(self):
        lp = LazyParser(3)

        for m in [lp.unwrap, lambda: lp.parse_type(list), lp.iter]:
            self.assertRaises(
                error.MalformedMessage,
                m)


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

    def test_neg_apply_struct_invalid_identifier(self):
        for badid in InvalidIdentifiers:
            lp = LazyParser({badid: 'thingy'})

            def check(**_):
                self._fail_if_called()

            self.assertRaises(
                error.InvalidIdentifier,
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

    def test_neg_invalid_tag_syntax(self):
        for badtag in InvalidIdentifiers:
            lp = LazyParser([badtag, 'value'])

            self.assertRaises(
                error.InvalidIdentifier,
                lp.apply_variant,
                foo=lambda _: self.fail('variant should not have applied.'))


class LazyParser_path (TestCase):
    def test_neg_path_in_exception(self):
        lp = LazyParser(
            {'messages':
             ['@LIST',
              None,
              ['fruit', {'name': 'banana'}]]})
        self.assertEqual(lp._path, '')

        messages = lp.apply_struct(lambda messages: messages)
        self.assertEqual(messages._path, '.messages')

        variant = list(messages.iter())[1]
        self.assertEqual(variant._path, '.messages[1]')

        name = variant.apply_variant_struct(fruit=lambda name: name)
        self.assertEqual(name._path, '.messages[1]/fruit.name')

        try:
            name.parse_type(int)
        except error.MalformedMessage as mm:
            self.assertEqual('.messages[1]/fruit.name', mm.path)
