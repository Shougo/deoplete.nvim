import deoplete.util as util
from deoplete.filter.converter_remove_overlap import overlap_length
import deoplete.filter.matcher_fuzzy
import deoplete.filter.matcher_full_fuzzy

def test_overlap_length():
    assert overlap_length('foo bar', 'bar baz') == 3
    assert overlap_length('foobar', 'barbaz') == 3
    assert overlap_length('foob', 'baz') == 1
    assert overlap_length('foobar', 'foobar') == 6
    assert overlap_length('тест', 'ст') == len('ст')

def test_charwidth():
    assert util.charwidth('f') == 1
    assert util.charwidth('あ') == 2

def test_strwidth():
    assert util.strwidth('foo bar') == 7
    assert util.strwidth('あいうえ') == 8
    assert util.strwidth('fooあい') == 7

def test_truncate():
    assert util.truncate('foo bar', 3) == 'foo'
    assert util.truncate('fooあい', 5) == 'fooあ'
    assert util.truncate('あいうえ', 4) == 'あい'
    assert util.truncate('fooあい', 4) == 'foo'

def test_skipping():
    assert util.truncate_skipping('foo bar', 3, '..', 3) == '..bar'
    assert util.truncate_skipping('foo bar', 6, '..', 3) == 'f..bar'
    assert util.truncate_skipping('fooあい', 5, '..', 3) == 'f..い'
    assert util.truncate_skipping('あいうえ', 6, '..', 2) == 'あ..え'


def test_matcher_fuzzy():
    f = deoplete.filter.matcher_fuzzy.Filter(None)

    assert f.name == 'matcher_fuzzy'
    assert f.description == 'fuzzy matcher'

    ctx = {
        'complete_str': '',
        'ignorecase': True,
        'camelcase': True,
        'is_sorted': False,
        'candidates': [
            { 'word': 'FooBar' },
            { 'word': 'foobar' },
            { 'word': 'aFooBar' },
        ]
    }
    assert f.filter(ctx) == [
        { 'word': 'FooBar' },
        { 'word': 'foobar' },
        { 'word': 'aFooBar' },
    ]

    ctx = {
        'complete_str': 'FOBR',
        'ignorecase': True,
        'camelcase': True,
        'is_sorted': False,
        'candidates': [
            { 'word': 'FooBar' },
            { 'word': 'foobar' },
            { 'word': 'aFooBar' },
        ]
    }
    assert f.filter(ctx) == [
        { 'word': 'FooBar' },
        { 'word': 'foobar' },
    ]

    ctx = {
        'complete_str': 'foBr',
        'ignorecase': False,
        'camelcase': True,
        'is_sorted': False,
        'candidates': [
            { 'word': 'FooBar' },
            { 'word': 'foobar' },
            { 'word': 'aFooBar' },
        ]
    }
    assert f.filter(ctx) == [
        { 'word': 'FooBar' },
    ]

    ctx = {
        'complete_str': 'fobr',
        'ignorecase': True,
        'camelcase': False,
        'is_sorted': False,
        'candidates': [
            { 'word': 'FooBar' },
            { 'word': 'foobar' },
            { 'word': 'aFooBar' },
            { 'word': 'fooBar' },
        ]
    }
    assert f.filter(ctx) == [
        { 'word': 'FooBar' },
        { 'word': 'foobar' },
        { 'word': 'fooBar' },
    ]

    ctx = {
        'complete_str': 'fobr',
        'ignorecase': False,
        'camelcase': False,
        'is_sorted': False,
        'candidates': [
            { 'word': 'FooBar' },
            { 'word': 'foobar' },
            { 'word': 'aFooBar' },
            { 'word': 'fooBar' },
        ]
    }
    assert f.filter(ctx) == [
        { 'word': 'foobar' },
    ]


def test_matcher_full_fuzzy():
    f = deoplete.filter.matcher_full_fuzzy.Filter(None)

    assert f.name == 'matcher_full_fuzzy'
    assert f.description == 'full fuzzy matcher'

    ctx = {
        'complete_str': '',
        'ignorecase': True,
        'camelcase': True,
        'is_sorted': False,
        'candidates': [
            { 'word': 'FooBar' },
            { 'word': 'foobar' },
            { 'word': 'aFooBar' },
        ]
    }
    assert f.filter(ctx) == [
        { 'word': 'FooBar' },
        { 'word': 'foobar' },
        { 'word': 'aFooBar' },
    ]

    ctx = {
        'complete_str': 'FOBR',
        'ignorecase': True,
        'camelcase': True,
        'is_sorted': False,
        'candidates': [
            { 'word': 'FooBar' },
            { 'word': 'foobar' },
            { 'word': 'aFooBar' },
        ]
    }
    assert f.filter(ctx) == [
        { 'word': 'FooBar' },
        { 'word': 'foobar' },
        { 'word': 'aFooBar' },
    ]

    ctx = {
        'complete_str': 'foBr',
        'ignorecase': False,
        'camelcase': True,
        'is_sorted': False,
        'candidates': [
            { 'word': 'FooBar' },
            { 'word': 'foobar' },
            { 'word': 'aFooBar' },
            { 'word': 'afoobar' },
        ]
    }
    assert f.filter(ctx) == [
        { 'word': 'FooBar' },
        { 'word': 'aFooBar' },
    ]

    ctx = {
        'complete_str': 'fobr',
        'ignorecase': True,
        'camelcase': False,
        'is_sorted': False,
        'candidates': [
            { 'word': 'FooBar' },
            { 'word': 'foobar' },
            { 'word': 'aFooBar' },
            { 'word': 'fooBar' },
        ]
    }
    assert f.filter(ctx) == [
        { 'word': 'FooBar' },
        { 'word': 'foobar' },
        { 'word': 'aFooBar' },
        { 'word': 'fooBar' },
    ]

    ctx = {
        'complete_str': 'fobr',
        'ignorecase': False,
        'camelcase': False,
        'is_sorted': False,
        'candidates': [
            { 'word': 'FooBar' },
            { 'word': 'foobar' },
            { 'word': 'aFooBar' },
            { 'word': 'fooBar' },
            { 'word': 'afoobar' },
        ]
    }
    assert f.filter(ctx) == [
        { 'word': 'foobar' },
        { 'word': 'afoobar' },
    ]
