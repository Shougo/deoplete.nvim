from unittest import TestCase
from nose.tools import eq_
from deoplete.util import (
    fuzzy_escape, charwidth, strwidth, truncate, truncate_skipping)
from deoplete.filters.converter_remove_overlap import overlap_length


class FilterTestCase(TestCase):

    def test_fuzzy_escapse(self):
        eq_(fuzzy_escape('foo', 0), 'f[^f]*o[^o]*o[^o]*')
        eq_(fuzzy_escape('foo', 1), 'f[^f]*o[^o]*o[^o]*')
        eq_(fuzzy_escape('Foo', 1), 'F[^F]*[oO].*[oO].*')

    def test_overlap_length(self):
        eq_(overlap_length('foo bar', 'bar baz'), 3)
        eq_(overlap_length('foobar', 'barbaz'), 3)
        eq_(overlap_length('foob', 'baz'), 1)
        eq_(overlap_length('foobar', 'foobar'), 6)
        eq_(overlap_length('тест', 'ст'), len('ст'))

    def test_charwidth(self):
        eq_(charwidth('f'), 1)
        eq_(charwidth('あ'), 2)

    def test_strwidth(self):
        eq_(strwidth('foo bar'), 7)
        eq_(strwidth('あいうえ'), 8)
        eq_(strwidth('fooあい'), 7)

    def test_truncate(self):
        eq_(truncate('foo bar', 3), 'foo')
        eq_(truncate('fooあい', 5), 'fooあ')
        eq_(truncate('あいうえ', 4), 'あい')
        eq_(truncate('fooあい', 4), 'foo')

    def test_skipping(self):
        eq_(truncate_skipping('foo bar', 3, '..', 3), '..bar')
        eq_(truncate_skipping('foo bar', 6, '..', 3), 'f..bar')
        eq_(truncate_skipping('fooあい', 5, '..', 3), 'f..い')
        eq_(truncate_skipping('あいうえ', 6, '..', 2), 'あ..え')
