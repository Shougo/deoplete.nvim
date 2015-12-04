# ============================================================================
# FILE: base.py
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
from abc import abstractmethod
import deoplete.util


class Base(object):

    def __init__(self, vim):
        self.vim = vim
        self.name = 'base'
        self.description = ''
        self.marker = ''
        self.min_pattern_length = -1
        self.matchers = ['matcher_fuzzy']
        self.sorters = ['sorter_rank']
        self.converters = ['converter_remove_overlap']
        self.filetypes = []
        self.is_bytepos = False
        self.rank = 100

    def get_complete_position(self, context):
        m = re.search(
            '(' + context['keyword_patterns'] + ')$', context['input'])
        return m.start() if m else -1

    @abstractmethod
    def gather_candidate(self, context):
        pass

    def debug(self, expr):
        deoplete.util.debug(self.vim, expr)
