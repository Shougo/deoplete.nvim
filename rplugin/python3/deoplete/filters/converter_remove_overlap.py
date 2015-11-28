# ============================================================================
# FILE: converter_remove_overlap.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license  {{{
#     Permission is hereby granted, free of charge, to any person obtaining
#     a copy of this software and associated documentation files (the
#     "Software"), to deal in the Software without restriction, including
#     without limitation the rights to use, copy, modify, merge, publish,
#     distribute, sublicense, and/or sell copies of the Software, and to
#     permit persons to whom the Software is furnished to do so, subject to
#     the following conditions:
#
#     The above copyright notice and this permission notice shall be included
#     in all copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#     OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#     MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#     IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#     CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#     TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#     SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# }}}
# ============================================================================

import re
from .base import Base


class Filter(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'converter_remove_overlap'
        self.description = 'remove overlap converter'

    def filter(self, context):
        m = re.match('\S+', context['next_input'])
        if not m:
            return context['candidates']
        next = m.group(0)
        for [overlap, candidate] in [
                [x, y] for x, y
                in [[overlap_length(x['word'], next), x]
                    for x in context['candidates']] if x > 0]:
            if 'abbr' not in candidate:
                candidate['abbr'] = candidate['word']
            candidate['word'] = candidate['word'][: -overlap]
        return [x for x in context['candidates']
                if x['word'] != context['complete_str']]


def overlap_length(left, right):
    pos = len(right)
    while pos > 0 and not left.endswith(right[: pos]):
        pos -= 1
    return pos
