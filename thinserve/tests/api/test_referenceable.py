from unittest import TestCase
from thinserve.api.referenceable import Referenceable


class ReferenceableTests (TestCase):
    def test_class_decorator_is_transparent(self):
        class C (object):
            pass

        self.assertIs(C, Referenceable(C))

        # Try the same with methods:
        class D (object):
            @Referenceable.Method
            def foo(self):
                return 'x'

        self.assertIs(D, Referenceable(D))

    def test_check(self):
        @Referenceable
        class C (object):
            pass

        i = C()

        self.failUnless(Referenceable._check(i))

        class D (object):
            pass

        j = D()

        self.failIf(Referenceable._check(j))

    def test_pos_methods(self):

        @Referenceable
        class C (object):
            @Referenceable.Method
            def foo(self, x):
                return (self, x)

        i = C()

        self.failUnless(Referenceable._check(i))
        self.assertEqual((i, 42), i.foo(42))

        brm = Referenceable._get_bound_methods(i)
        self.assertEqual(['foo'], brm.keys())
        self.assertEqual((i, 17), brm['foo'](x=17))
