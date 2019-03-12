# ============================================================================
# FILE: sorter_rank.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re

from deoplete.base.filter import Base
from deoplete.util import getlines


LINES_ABOVE = 100
LINES_BELOW = 100


class Filter(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'sorter_rank'
        self.description = 'rank sorter'
        self._cache = {}

    def on_event(self, context):
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

    def filter(self, context):
        complete_str = context['complete_str'].lower()

        def compare(x):
            matched = int(complete_str in x['word'].lower())
            mru = self._cache.get(x['word'], 0)
            return -(matched * 40 + mru * 20)
        return sorted(context['candidates'], key=compare)
