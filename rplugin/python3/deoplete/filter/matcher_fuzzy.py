# ============================================================================
# FILE: matcher_fuzzy.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from .base import Base
from deoplete.util import fuzzy_match


class Filter(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'matcher_fuzzy'
        self.description = 'fuzzy matcher'

    def filter(self, context, ensure_same_prefix=True):
        complete_str = context['complete_str']
        if context['ignorecase']:
            complete_str = complete_str.lower()

        candidates = context['candidates']
        camelcase = context['camelcase']
        if context['ignorecase']:
            return [x for x in candidates
                    if fuzzy_match(x['word'].lower(), complete_str, camelcase,
                                   ensure_same_prefix)]
        else:
            return [x for x in candidates
                    if fuzzy_match(x['word'], complete_str, camelcase,
                                   ensure_same_prefix)]
