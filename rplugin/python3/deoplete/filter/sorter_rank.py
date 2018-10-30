# ============================================================================
# FILE: sorter_rank.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re

from deoplete.filter.base import Base
from deoplete.util import getlines


LINES_ABOVE = 100
LINES_BELOW = 100


class Filter(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'sorter_rank'
        self.description = 'rank sorter'
        self._cache = set()

    def on_event(self, context):
        line = context['position'][1]
        lines = getlines(self.vim,
                         max([1, line - LINES_ABOVE]), line + LINES_BELOW)
        self._cache = set(re.findall(context['keyword_pattern'],
                                     '\n'.join(lines)))

    def filter(self, context):
        if not context['complete_str']:
            return context['candidates']

        complete_str = context['complete_str'].lower()
        input_len = len(complete_str)

        def compare(x):
            if x['word'] in self._cache:
                return -1
            else:
                return abs(x['word'].lower().find(
                    complete_str, 0, input_len))
        return sorted(context['candidates'], key=compare)
