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
        p = re.compile(context['keyword_patterns'])

        try:
            if (self.vim.current.buffer.number in self.__buffers) and len(
                    self.vim.current.buffer) > self.__max_lines:
                line = context['position'][1]
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
        except UnicodeDecodeError:
            return []

        buffers = [x['candidates'] for x in self.__buffers.values()
                   if x['filetype'] in context['filetypes']]
        if not buffers:
            return []

        return [{'word': x} for x in
                functools.reduce(operator.add, buffers)]
