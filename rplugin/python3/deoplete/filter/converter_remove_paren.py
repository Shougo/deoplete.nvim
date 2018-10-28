# ============================================================================
# FILE: converter_remove_paren.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from deoplete.filter.base import Base


class Filter(Base):
    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'converter_remove_paren'
        self.description = 'remove parentheses converter'

    def filter(self, context):
        p = re.compile(r'\(\)?$')
        for candidate in [x for x in context['candidates']
                          if p.search(x['word'])]:
            candidate['word'] = re.sub(r'\(\)?$', '', candidate['word'])
        return context['candidates']
