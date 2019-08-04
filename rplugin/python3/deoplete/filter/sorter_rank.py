# ============================================================================
# FILE: sorter_rank.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
import typing

from deoplete.base.filter import Base
from deoplete.util import getlines
from deoplete.util import Nvim, UserContext, Candidates, Candidate


LINES_ABOVE = 100
LINES_BELOW = 100


class Filter(Base):

    def __init__(self, vim: Nvim) -> None:
        super().__init__(vim)

        self.name = 'sorter_rank'
        self.description = 'rank sorter'
        self._cache: typing.Dict[str, int] = {}

    def on_event(self, context: UserContext) -> None:
        line = context['position'][1]
        lines = getlines(self.vim,
                         max([1, line - LINES_ABOVE]), line + LINES_BELOW)

        self._cache = {}
        for m in re.finditer(context['keyword_pattern'], '\n'.join(lines)):
            k = m.group(0)
            if k in self._cache:
                self._cache[k] += 1
            else:
                self._cache[k] = 1

    def filter(self, context: UserContext) -> Candidates:
        complete_str = context['complete_str'].lower()

        def compare(x: Candidate) -> int:
            matched = int(complete_str in x['word'].lower())
            mru = self._cache.get(x['word'], 0)
            return -(matched * 40 + mru * 20)
        return sorted(context['candidates'], key=compare)
