# ============================================================================
# FILE: matcher_fuzzy.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from .base import Base
from deoplete.util import fuzzy_escape


class Filter(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'matcher_fuzzy'
        self.description = 'fuzzy matcher'

    def filter(self, context):
        complete_str = context['complete_str']
        if context['ignorecase']:
            complete_str = complete_str.lower()
        p = re.compile(fuzzy_escape(complete_str, context['camelcase']))
        if context['ignorecase']:
            return [x for x in context['candidates']
                    if p.match(x['word'].lower())]
        else:
            return [x for x in context['candidates']
                    if p.match(x['word'])]
