# ============================================================================
# FILE: file.py
# AUTHOR: Felipe Morales <hel.sheep at gmail.com>
#         Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import os
import re
from os.path import exists, dirname
from .base import Base
from deoplete.util import expand


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'file'
        self.mark = '[F]'
        self.min_pattern_length = 0
        self.rank = 150
        self.__isfname = ''

    def on_init(self, context):
        self.__buffer_path = context['vars'].get(
            'deoplete#file#enable_buffer_path', 0)

    def on_event(self, context):
        self.__isfname = self.vim.call(
            'deoplete#util#vimoption2python_not',
            self.vim.options['isfname'])

    def get_complete_position(self, context):
        pos = context['input'].rfind('/')
        return pos if pos < 0 else pos + 1

    def gather_candidates(self, context):
        if not self.__isfname:
            return []

        p = self.__longest_path_that_exists(context, context['input'])
        if p in (None, []) or p == '/' or re.search('//+$', p):
            return []
        complete_str = self.__substitute_path(context, dirname(p) + '/')
        if not os.path.isdir(complete_str):
            return []
        hidden = context['complete_str'].find('.') == 0
        contents = [[], []]
        try:
            for item in sorted(os.listdir(complete_str), key=str.lower):
                if not hidden and item[0] == '.':
                    continue
                contents[not os.path.isdir(complete_str + item)].append(item)
        except PermissionError:
            pass

        dirs, files = contents
        return [{'word': x, 'abbr': x + '/'} for x in dirs
                ] + [{'word': x} for x in files]

    def __longest_path_that_exists(self, context, input_str):
        input_str = re.sub(r'[^/]*$', '', input_str)
        data = re.split(r'((?:%s+|(?:(?<![\w\s/\.])(?:~|\.{1,2})?/)+))' %
                        self.__isfname, input_str)
        data = [''.join(data[i:]) for i in range(len(data))]
        existing_paths = sorted(filter(lambda x: exists(
            dirname(self.__substitute_path(context, x))), data))
        return existing_paths[-1] if existing_paths else None

    def __substitute_path(self, context, path):
        m = re.match(r'(\.{1,2})/+', path)
        if m:
            if self.__buffer_path and context['bufpath']:
                base = context['bufpath']
            else:
                base = os.path.join(context['cwd'], 'x')

            for _ in m.group(1):
                base = dirname(base)
            return os.path.abspath(os.path.join(
                base, path[len(m.group(0)):])) + '/'
        return expand(path)
