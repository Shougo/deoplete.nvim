import deoplete.util as util


def test_pos():
    assert util.bytepos2charpos('utf-8', 'foo bar', 3) == 3
    assert util.bytepos2charpos('utf-8', 'あああ', 3) == 1
    assert util.charpos2bytepos('utf-8', 'foo bar', 3) == 3
    assert util.charpos2bytepos('utf-8', 'あああ', 3) == 9

def test_custom():
    custom = {'_': {'mark': ''}, 'java': {'converters': []}}
    assert util.get_custom(custom, 'java', 'mark', 'foobar') == ''
    assert util.get_custom(custom, 'java', 'converters', 'foobar') == []
    assert util.get_custom(custom, 'foo', 'mark', 'foobar') == ''
    assert util.get_custom(custom, 'foo', 'converters', 'foobar') == 'foobar'


def test_globruntime():
    assert util.globruntime('/usr', 'bin') == ['/usr/bin']
