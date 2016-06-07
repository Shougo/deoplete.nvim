from unittest import TestCase
from nose.tools import eq_
from deoplete.util import (
    bytepos2charpos, charpos2bytepos)


class UtilTestCase(TestCase):

    def test_pos(self):
        eq_(bytepos2charpos('utf-8', 'foo bar', 3), 3)
        eq_(bytepos2charpos('utf-8', 'あああ', 3), 1)
        eq_(charpos2bytepos('utf-8', 'foo bar', 3), 3)
        eq_(charpos2bytepos('utf-8', 'あああ', 3), 9)
