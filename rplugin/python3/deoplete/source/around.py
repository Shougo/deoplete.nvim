import re
from .base import Base

from deoplete.logger import getLogger
from deoplete.util import parse_buffer_pattern

logger = getLogger('around')

ABOVE_LINES = 20
BELOW_LINES = 20


class Source(Base):
    def __init__(self, vim):
        super().__init__(vim)
        self.name = 'around'
        self.mark = '[~]'
        self.rank = 800

    def gather_candidates(self, context):
        candidates = list()

        # 20 lines above
        lnum = context['position'][1]
        words = parse_buffer_pattern(
                        reversed(self.vim.call('getline',
                                               max([1, lnum - ABOVE_LINES]),
                                               lnum)),
                        context['keyword_patterns'],
                        context['complete_str'])
        candidates.extend([{'word': x, 'menu': 'A'} for x in words])

        # grab ':changes' command output
        p = re.compile(r'[\s\d]+')
        changes = self.vim.call('execute', 'changes').split('\n')
        lines = set()
        for change in changes:
            m = p.search(change)
            if m:
                line = change[m.span()[1]:]
                if line and line != '-invalid-':
                    lines.add(line)

        words = parse_buffer_pattern(lines,
                                     context['keyword_patterns'],
                                     context['complete_str'])
        candidates.extend([{'word': x, 'menu': 'C'} for x in words])

        # 20 lines below
        words = parse_buffer_pattern(
                        self.vim.call('getline', lnum, lnum + BELOW_LINES),
                        context['keyword_patterns'],
                        context['complete_str'])
        candidates.extend([{'word': x, 'menu': 'B'} for x in words])

        return candidates
