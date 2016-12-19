import re
from .base import Base

from deoplete.logger import getLogger
from deoplete.util import parse_buffer_pattern

logger = getLogger('around')


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
                                               max([1, lnum - 20]),
                                               lnum)),
                        context['keyword_patterns'],
                        context['complete_str'])
        candidates.extend([{'word': x, 'menu': 'A'} for x in words])

        # grab ':changes' command output
        self.vim.command('exec "redir => g:deoplete_recent_changes"')
        self.vim.command('silent! changes')
        self.vim.command('redir END')

        p = re.compile('[\s\d]+')
        changes = self.vim.eval('g:deoplete_recent_changes').split('\n')
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
                        self.vim.call('getline', lnum, lnum + 20),
                        context['keyword_patterns'],
                        context['complete_str'])
        candidates.extend([{'word': x, 'menu': 'B'} for x in words])

        return candidates
