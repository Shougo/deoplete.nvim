# ============================================================================
# FILE: converter_remove_paren.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from .base import Base


class Filter(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'converter_remove_paren'
        self.description = 'remove parentheses converter'

    def filter(self, context):
        p = re.compile('\(\)?$')
        for candidate in [x for x in context['candidates']
                          if p.search(x['word'])]:
            candidate['word'] = re.sub('\(\)?$', '', candidate['word'])
        return context['candidates']
