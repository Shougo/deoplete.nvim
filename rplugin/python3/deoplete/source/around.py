# ============================================================================
# FILE: around.py
# AUTHOR: Khalidov Oleg <brooth at gmail.com>
# License: MIT license
# ============================================================================

import re

from .base import Base
from deoplete.util import parse_buffer_pattern, getlines

LINES_ABOVE = 20
LINES_BELOW = 20


class Source(Base):
    def __init__(self, vim):
        super().__init__(vim)
        self.name = 'around'
        self.mark = '[~]'
        self.rank = 300

    def gather_candidates(self, context):
        line = context['position'][1]
        candidates = []

        # lines above
        keyword_pattern = self.vim.call(
            'deoplete#util#get_keyword_pattern',
            context['filetype'], self.keyword_patterns)
        words = parse_buffer_pattern(
            reversed(getlines(self.vim, max([1, line - LINES_ABOVE]), line)),
            keyword_pattern)
        candidates += [{'word': x, 'menu': 'A'} for x in words]

        # grab ':changes' command output
        p = re.compile(r'[\s\d]+')
        lines = set()
        for change_line in [x[p.search(x).span()[1]:] for x
                            in self.vim.call(
                                'execute', 'changes').split('\n')
                            if p.search(x)]:
            if change_line and change_line != '-invalid-':
                lines.add(change_line)

        words = parse_buffer_pattern(lines, keyword_pattern)
        candidates += [{'word': x, 'menu': 'C'} for x in words]

        # lines below
        words = parse_buffer_pattern(
            getlines(self.vim, line, line + LINES_BELOW), keyword_pattern)
        candidates += [{'word': x, 'menu': 'B'} for x in words]

        return candidates
