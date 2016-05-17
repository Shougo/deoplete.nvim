# ============================================================================
# FILE: member.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from .base import Base

import re
from deoplete.util import \
    get_buffer_config, convert2list, parse_buffer_pattern


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'member'
        self.mark = '[M]'
        self.min_pattern_length = 0

        self.__object_pattern = r'[a-zA-Z_]\w*(?:\(\)?)?'
        self.__prefix = ''

    def get_complete_position(self, context):
        # Check member prefix pattern.
        for prefix_pattern in convert2list(
                get_buffer_config(self.vim, context['filetype'],
                                  'b:deoplete_member_prefix_patterns',
                                  'g:deoplete#member#prefix_patterns',
                                  'g:deoplete#member#_prefix_patterns')):
            m = re.search(self.__object_pattern + prefix_pattern + r'\w*$',
                          context['input'])
            if m is None or prefix_pattern == '':
                continue
            self.__prefix = re.sub(r'\w*$', '', m.group(0))
            return re.search(r'\w*$', context['input']).start()
        return -1

    def gather_candidates(self, context):
        return [{'word': x} for x in
                parse_buffer_pattern(
                    self.vim.current.buffer,
                    r'(?<=' + re.escape(self.__prefix) + r')\w+(?:\(\)?)?',
                    context['complete_str']
                )
                if x != context['complete_str']]
