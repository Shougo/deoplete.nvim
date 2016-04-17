# ============================================================================
# FILE: buffer.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
import functools
import operator
from .base import Base


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'buffer'
        self.mark = '[B]'
        self.__buffers = {}
        self.__max_lines = 5000

    def gather_candidates(self, context):
        self.__make_cache(context, self.vim.current.buffer.number)

        buffers = [x['candidates'] for x in self.__buffers.values()
                   if x['filetype'] in context['filetypes']]
        if not buffers:
            return []

        return [{'word': x} for x in
                functools.reduce(operator.add, buffers)]

    def on_buffer(self, context):
        if (self.vim.current.buffer.number
                not in self.__buffers and
                self.vim.current.buffer.options['modifiable']):
            self.__make_cache(context, self.vim.current.buffer.number)

    def __make_cache(self, context, bufnr):
        p = re.compile(context['keyword_patterns'])

        bufnr -= 1
        try:
            if (bufnr in self.__buffers) and len(
                    self.vim.buffers[bufnr]) > self.__max_lines:
                line = context['position'][1]
                self.__buffers[bufnr][
                    'candidates'] += functools.reduce(operator.add, [
                        p.findall(x) for x in self.vim.buffers[bufnr][
                            max([0, line - 500]): line + 500]
                    ])
            else:
                self.__buffers[bufnr] = {
                    'filetype': context['filetype'],
                    'candidates': functools.reduce(operator.add, [
                        p.findall(x) for x in self.vim.buffers[bufnr]
                    ]),
                }
        except UnicodeDecodeError:
            return []
