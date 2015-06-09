from unittest import TestCase
from nose.tools import ok_, eq_
from deoplete.filters.matcher_fuzzy import fuzzy_escape

class FilterTestCase(TestCase):
    def test_fuzzy_escapse(self):
        eq_(fuzzy_escape('foo'), 'f.*o.*o.*')

