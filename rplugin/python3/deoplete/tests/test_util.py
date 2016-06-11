from unittest import TestCase
from nose.tools import eq_
from deoplete.util import (
    bytepos2charpos, charpos2bytepos, get_custom, globruntime)


class UtilTestCase(TestCase):

    def test_pos(self):
        eq_(bytepos2charpos('utf-8', 'foo bar', 3), 3)
        eq_(bytepos2charpos('utf-8', 'あああ', 3), 1)
        eq_(charpos2bytepos('utf-8', 'foo bar', 3), 3)
        eq_(charpos2bytepos('utf-8', 'あああ', 3), 9)

    def test_custom(self):
        custom = {'_': {'mark': ''}, 'java': {'converters': []}}
        eq_(get_custom(custom, 'java', 'mark', 'foobar'), '')
        eq_(get_custom(custom, 'java', 'converters', 'foobar'), [])
        eq_(get_custom(custom, 'foo', 'mark', 'foobar'), '')
        eq_(get_custom(custom, 'foo', 'converters', 'foobar'), 'foobar')

    def test_globruntime(self):
        eq_(globruntime('/usr', 'lib'), ['/usr/lib'])
