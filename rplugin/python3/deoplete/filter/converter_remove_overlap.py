# ============================================================================
# FILE: converter_remove_overlap.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from deoplete.base.filter import Base


class Filter(Base):
    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'converter_remove_overlap'
        self.description = 'remove overlap converter'

    def filter(self, context):
        if not context['next_input']:
            return context['candidates']
        m = re.match(r'\S+', context['next_input'])
        if not m:
            return context['candidates']
        next_input = m.group(0)
        for [overlap, candidate] in [
                [x, y] for x, y
                in [[overlap_length(x['word'], next_input), x]
                    for x in context['candidates']] if x > 0]:
            if 'abbr' not in candidate:
                candidate['abbr'] = candidate['word']
            candidate['word'] = candidate['word'][: -overlap]
        return context['candidates']


def overlap_length(left, right):
    pos = len(right)
    while pos > 0 and not left.endswith(right[: pos]):
        pos -= 1
    return pos
