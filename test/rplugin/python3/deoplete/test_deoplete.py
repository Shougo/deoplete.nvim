from unittest import mock

import pytest

from deoplete.deoplete import Deoplete


def _deoplete(text):
    d = Deoplete.__new__(Deoplete)
    d._vim = mock.Mock(vars={'deoplete#_prev_completion': {
        'candidates': [], 'time': 0}})
    d._vim.call.return_value = 0
    d._context = mock.Mock()
    d._context.get.return_value = {
        'input': text, 'next_input': '', 'encoding': 'utf-8',
        'event': 'TextChangedI', 'time': 1}
    d._check_recache = mock.Mock()
    d._prev_results = {}
    d._prev_input = d._prev_next_input = ''
    return d


# 'é' is 2 bytes: positions are byte offsets
@pytest.mark.parametrize('text,start', [('foo.ba', 0), ('é.foo.ba', 3)])
def test_merge_results_prefix(text, start):
    d = _deoplete(text)
    d._parents = [mock.Mock()]
    d._parents[0].merge_results.return_value = (False, False, [
        {'complete_position': start, 'rank': 100,
         'candidates': [{'word': 'foo.bar'}]},
        {'complete_position': start + 4, 'rank': 50,
         'candidates': [{'word': 'bar'}]},
    ])
    # The second call reuses the cached result
    for _ in range(2):
        words = [c['word'] for c in d._merge_results(d._context.get())[3]]
        assert words == ['foo.bar', 'foo.bar']


@pytest.mark.parametrize('text,position,complete_str',
                         [('é.foo', 3, 'foo'), ('é', -1, '')])
def test_complete_str(text, position, complete_str):
    d = _deoplete(text)
    d._merge_results = mock.Mock(return_value=(False, False, position, []))
    d.completion_begin({'event': 'TextChangedI'})
    assert d._vim.vars['deoplete#_context']['complete_str'] == complete_str
