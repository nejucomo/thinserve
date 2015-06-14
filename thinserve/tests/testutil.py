from textwrap import dedent
from pprint import pformat


def check_mock(testcase, mockobj, expectedcalls):
    check_lists_equal(testcase, expectedcalls, mockobj.mock_calls)


def check_lists_equal(testcase, expected, actual):
    tmpl = dedent('''
        List idx {}:
          expected: {!r}
          !=actual: {!r}
        Expected list:
        {}
        Actual list:
        {}
    '''.rstrip()) + '\n'

    i = -1
    for i, (x, y) in enumerate(zip(expected, actual)):
        testcase.assertEqual(
            x, y,
            tmpl.format(
                i, x, y,
                indent(pformat(expected)),
                indent(pformat(actual))))

    for name, l in [('missing expected', expected),
                    ('unexpected actual', actual)]:

        missing = l[i+1:]
        testcase.failUnless(
            len(missing) == 0,
            '{} elements {!r}'.format(name, missing))


def indent(s, cols=2):
    prefix = ' ' * cols
    return prefix + s.replace('\n', '\n' + prefix)


class EqCb (object):
    """Useful for passing predicates into check_mock call parameters."""
    def __init__(self, cb):
        self._cb = cb

    def __eq__(self, other):
        return self._cb(other)

    def __repr__(self):
        return '<EqCb {!r}>'.format(self._cb)
