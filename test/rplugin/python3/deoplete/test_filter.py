import deoplete.util as util

def test_fuzzy_escapse(self):
    assert fuzzy_escape('foo', 0) == 'f[^f]*o[^o]*o[^o]*'
    assert fuzzy_escape('foo', 1) == 'f[^f]*o[^o]*o[^o]*'
    assert fuzzy_escape('Foo', 1) == 'F[^F]*[oO].*[oO].*'

def test_overlap_length(self):
    assert overlap_length('foo bar', 'bar baz') == 3
    assert overlap_length('foobar', 'barbaz') == 3
    assert overlap_length('foob', 'baz') == 1
    assert overlap_length('foobar', 'foobar') == 6
    assert overlap_length('тест', 'ст') == len('ст')

def test_charwidth(self):
    assert charwidth('f') == 1
    assert charwidth('あ') == 2

def test_strwidth(self):
    assert strwidth('foo bar') == 7
    assert strwidth('あいうえ') == 8
    assert strwidth('fooあい') == 7

def test_truncate(self):
    assert truncate('foo bar', 3) == 'foo'
    assert truncate('fooあい', 5) == 'fooあ'
    assert truncate('あいうえ', 4) == 'あい'
    assert truncate('fooあい', 4) == 'foo'

def test_skipping(self):
    assert truncate_skipping('foo bar', 3, '..', 3) == '..bar'
    assert truncate_skipping('foo bar', 6, '..', 3) == 'f..bar'
    assert truncate_skipping('fooあい', 5, '..', 3) == 'f..い'
    assert truncate_skipping('あいうえ', 6, '..', 2) == 'あ..え'
