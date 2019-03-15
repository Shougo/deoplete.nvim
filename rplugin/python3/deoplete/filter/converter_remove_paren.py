# ============================================================================
# FILE: converter_remove_paren.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from deoplete.base.filter import Base


class Filter(Base):
    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'converter_remove_paren'
        self.description = 'remove parentheses converter'

    def filter(self, context):
        for candidate in [x for x in context['candidates']
                          if '(' in x['word']]:
            candidate['word'] = re.sub(r'\(.*\)(\$\d+)?', '',
                                       candidate['word'])
        return context['candidates']
