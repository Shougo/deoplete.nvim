from unittest import TestCase
from nose.tools import eq_
from deoplete.util import fuzzy_escape
from deoplete.filters.converter_remove_overlap import overlap_length


class FilterTestCase(TestCase):

    def test_fuzzy_escapse(self):
        eq_(fuzzy_escape('foo', 0), 'f.*o.*o.*')
        eq_(fuzzy_escape('foo', 1), 'f.*o.*o.*')
        eq_(fuzzy_escape('Foo', 1), 'F.*[oO].*[oO].*')

    def test_overlap_length(self):
        eq_(overlap_length('foo bar', 'bar baz'), 3)
        eq_(overlap_length('foobar', 'barbaz'), 3)
        eq_(overlap_length('foob', 'baz'), 1)
        eq_(overlap_length('foobar', 'foobar'), 6)
        eq_(overlap_length('тест', 'ст'), len('ст'))
