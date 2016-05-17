# ============================================================================
# FILE: buffer.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from .base import Base

import functools
import operator
from deoplete.util import parse_buffer_pattern


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'buffer'
        self.mark = '[B]'
        self.__buffers = {}
        self.__max_lines = 5000

    def on_event(self, context):
        if not self.vim.current.buffer.options['modifiable']:
            return
        if ((self.vim.current.buffer.number not in self.__buffers) or
                context['event'] == 'BufWritePost'):
            self.__make_cache(context, self.vim.current.buffer)

    def gather_candidates(self, context):
        self.__make_cache(context, self.vim.current.buffer)

        buffers = [x['candidates'] for x in self.__buffers.values()
                   if x['filetype'] in context['filetypes']]
        if not buffers:
            return []

        return [{'word': x} for x in
                functools.reduce(operator.add, buffers)]

    def __make_cache(self, context, buffer):
        bufnr = buffer.number
        try:
            if (bufnr in self.__buffers and
                    context['event'] != 'BufWritePost' and
                    len(buffer) > self.__max_lines):
                line = context['position'][1]
                self.__buffers[bufnr][
                    'candidates'] += parse_buffer_pattern(
                        buffer[max([0, line-500]):line+500],
                        context['keyword_patterns'],
                        context['complete_str'])
                self.__buffers[bufnr]['candidates'] = list(
                    set(self.__buffers[bufnr]['candidates']))
            else:
                self.__buffers[bufnr] = {
                    'filetype': context['filetype'],
                    'candidates': parse_buffer_pattern(
                        buffer,
                        context['keyword_patterns'],
                        context['complete_str'])
                }
        except UnicodeDecodeError:
            return []
