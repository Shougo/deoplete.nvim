# ============================================================================
# FILE: matcher_fuzzy.py
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

        self.name = 'matcher_fuzzy'
        self.description = 'fuzzy matcher'

    def filter(self, context):
        complete_str = context['complete_str']
        if context['ignorecase']:
            complete_str = complete_str.lower()
        p = re.compile(fuzzy_escape(complete_str))
        input_len = len(complete_str)
        return [x for x in context['candidates']
                if len(x['word']) > input_len and p.match(x['word'].lower())
                ] if context['ignorecase'] \
            else [x for x in context['candidates']
                  if len(x['word']) > input_len and p.match(x['word'])]


def fuzzy_escape(string):
    # Escape string for python regexp.
    string = re.sub(r'([a-zA-Z0-9_])', r'\1.*', re.escape(string))
    return string
