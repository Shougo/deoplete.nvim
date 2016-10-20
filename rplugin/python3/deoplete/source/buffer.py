# ============================================================================
# FILE: buffer.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from .base import Base

import functools
import operator
from deoplete.util import parse_buffer_pattern, getlines


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'buffer'
        self.mark = '[B]'
        self.__buffers = {}
        self.__max_lines = 5000
        self.__abort_lines = 1000000

    def on_event(self, context):
        if ((context['bufnr'] not in self.__buffers) or
                context['event'] == 'BufWritePost'):
            self.__make_cache(context)

    def gather_candidates(self, context):
        self.__make_cache(context)

        buffers = [x['candidates'] for x in self.__buffers.values()
                   if x['filetype'] in context['filetypes']]
        if not buffers:
            return []

        return [{'word': x} for x in
                functools.reduce(operator.add, buffers)]

    def __make_cache(self, context):
        if (len(self.vim.current.buffer) > self.__abort_lines):
            return []

        try:
            if (context['bufnr'] in self.__buffers and
                    context['event'] != 'BufWritePost' and
                    len(self.vim.current.buffer) > self.__max_lines):
                line = context['position'][1]
                buffer = self.__buffers[context['bufnr']]
                buffer['candidates'] += parse_buffer_pattern(
                        getlines(self.vim, max([1, line-500]), line+500),
                        context['keyword_patterns'],
                        context['complete_str'])
                buffer['candidates'] = list(set(buffer['candidates']))
            else:
                self.__buffers[context['bufnr']] = {
                    'filetype': context['filetype'],
                    'candidates': parse_buffer_pattern(
                        getlines(self.vim),
                        context['keyword_patterns'],
                        context['complete_str'])
                }
        except UnicodeDecodeError:
            return []
