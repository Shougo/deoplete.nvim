# ============================================================================
# FILE: converter_remove_overlap.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re

from deoplete.base.filter import Base
from deoplete.util import Nvim, UserContext, Candidates


class Filter(Base):
    def __init__(self, vim: Nvim) -> None:
        super().__init__(vim)

        self.name = 'converter_remove_overlap'
        self.description = 'remove overlap converter'

    def filter(self, context: UserContext) -> Candidates:
        if not context['next_input']:
            return context['candidates']  # type: ignore
        m = re.match(r'\S+', context['next_input'])
        if not m:
            return context['candidates']  # type: ignore
        next_input = m.group(0)
        for [overlap, candidate] in [
                [x, y] for x, y
                in [[overlap_length(x['word'], next_input), x]
                    for x in context['candidates']] if x > 0]:
            if 'abbr' not in candidate:
                candidate['abbr'] = candidate['word']
            candidate['word'] = candidate['word'][: -overlap]
        return context['candidates']  # type: ignore


def overlap_length(left: str, right: str) -> int:
    pos = len(right)
    while pos > 0 and not left.endswith(right[: pos]):
        pos -= 1
    return pos
