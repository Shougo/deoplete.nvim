# ============================================================================
# FILE: member.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from .base import Base

import re
from deoplete.util import (
    convert2list, parse_buffer_pattern, set_pattern, getlines)


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'member'
        self.mark = '[M]'
        self.min_pattern_length = 0

        self._object_pattern = r'[a-zA-Z_]\w*(?:\(\)?)?'
        self._prefix = ''

        prefix_patterns = {}
        set_pattern(prefix_patterns,
                    '_', '\.')
        set_pattern(prefix_patterns,
                    'c,objc', ['\.', '->'])
        set_pattern(prefix_patterns,
                    'cpp,objcpp', ['\.', '->', '::'])
        set_pattern(prefix_patterns,
                    'perl,php', ['->'])
        set_pattern(prefix_patterns,
                    'ruby', ['\.', '::'])
        set_pattern(prefix_patterns,
                    'lua', ['\.', ':'])
        self.vars = {
            'prefix_patterns': prefix_patterns,
        }

    def get_complete_position(self, context):
        # Check member prefix pattern.
        for prefix_pattern in convert2list(
                self.get_filetype_var(
                    context['filetype'], 'prefix_patterns')):
            m = re.search(self._object_pattern + prefix_pattern + r'\w*$',
                          context['input'])
            if m is None or prefix_pattern == '':
                continue
            self._prefix = re.sub(r'\w*$', '', m.group(0))
            return re.search(r'\w*$', context['input']).start()
        return -1

    def gather_candidates(self, context):
        return [{'word': x} for x in
                parse_buffer_pattern(
                    getlines(self.vim),
                    r'(?<=' + re.escape(self._prefix) + r')\w+'
                )
                if x != context['complete_str']]
