# ============================================================================
# FILE: converter_auto_paren.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from .base import Base


class Filter(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'converter_auto_paren'
        self.description = 'auto add parentheses converter'

    def filter(self, context):
        p1 = re.compile('\(\)?$')
        p2 = re.compile('\(.*\)')
        for candidate in [
                x for x in context['candidates']
                if not p1.search(x['word']) and
                (('abbr' in x and p2.search(x['abbr'])) or
                 ('info' in x and p2.search(x['info'])))]:
            candidate['word'] += '('
        return context['candidates']
