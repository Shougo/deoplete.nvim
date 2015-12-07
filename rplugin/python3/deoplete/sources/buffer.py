# ============================================================================
# FILE: buffer.py
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
import operator
import functools
from .base import Base


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'buffer'
        self.mark = '[B]'
        self.__buffers = {}
        self.__max_lines = 5000

    def gather_candidates(self, context):
        p = re.compile(context['keyword_patterns'])

        if (self.vim.current.buffer.number in self.__buffers) and len(
                self.vim.current.buffer) > self.__max_lines:
            line = self.vim.current.window.cursor[0]
            self.__buffers[self.vim.current.buffer.number][
                'candidates'] += functools.reduce(operator.add, [
                    p.findall(x) for x in self.vim.current.buffer[
                        max([0, line - 500]): line + 500]
                ])
        else:
            self.__buffers[self.vim.current.buffer.number] = {
                'filetype': context['filetype'],
                'candidates': functools.reduce(operator.add, [
                    p.findall(x) for x in self.vim.current.buffer
                ]),
            }

        return [{'word': x} for x in
                functools.reduce(operator.add, [
                    x['candidates'] for x in self.__buffers.values()
                    if x['filetype'] in context['filetypes']])]
