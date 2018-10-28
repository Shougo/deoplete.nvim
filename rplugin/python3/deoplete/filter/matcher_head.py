# ============================================================================
# FILE: matcher_head.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from deoplete.filter.base import Base
from deoplete.util import binary_search_begin, binary_search_end


class Filter(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'matcher_head'
        self.description = 'head matcher'

    def filter(self, context):
        complete_str = context['complete_str']
        if context['ignorecase']:
            complete_str = complete_str.lower()

        if context['is_sorted']:
            begin = binary_search_begin(
                context['candidates'], complete_str)
            end = binary_search_end(
                context['candidates'], complete_str)
            if begin < 0 or end < 0:
                return []
            candidates = context['candidates'][begin:end+1]

            if context['ignorecase']:
                return candidates
        else:
            candidates = context['candidates']

        if context['ignorecase']:
            return [x for x in context['candidates']
                    if x['word'].lower().startswith(complete_str)]
        else:
            return [x for x in context['candidates']
                    if x['word'].startswith(complete_str)]
