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
from deoplete.util import \
    set_default, get_simple_buffer_config


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'file'
        self.mark = '[F]'
        self.min_pattern_length = 0
        self.rank = 150
        self.__isfname = ''

        set_default(self.vim, 'g:deoplete#file#enable_buffer_path', 0)

    def on_event(self, context):
        self.__isfname = self.vim.call(
            'deoplete#util#vimoption2python_not',
            self.vim.options['isfname'])

    def get_complete_position(self, context):
        pos = context['input'].rfind('/')
        return pos if pos < 0 else pos + 1

    def gather_candidates(self, context):
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
        data = [input_str]
        m = re.search(self.__isfname, input_str)
        if m and m.group(0) != '':
            data = re.split(self.__isfname, input_str)
        pos = [" ".join(data[i:]) for i in range(len(data))]
        existing_paths = list(filter(lambda x: exists(
            dirname(self.__substitute_path(context, x))), pos))
        if existing_paths and len(existing_paths) > 0:
            return sorted(existing_paths)[-1]
        return None

    def __substitute_path(self, context, path):
        buffer_path = get_simple_buffer_config(
            context,
            'deoplete_file_enable_buffer_path',
            'deoplete#file#enable_buffer_path')
        m = re.match(r'(\.+)/', path)
        if m:
            h = self.vim.funcs.repeat(':h', len(m.group(1)))
            return re.sub(r'^\.+',
                          self.vim.funcs.fnamemodify(
                              (context['bufname']
                               if buffer_path
                               else context['cwd']), ':p' + h),
                          path)
        m = re.match(r'~/', path)
        if m and os.environ.get('HOME'):
            return re.sub(r'^~', os.environ.get('HOME'), path)
        m = re.match(r'\$([A-Z_]+)/', path)
        if m and os.environ.get(m.group(1)):
            return re.sub(r'^\$[A-Z_]+', os.environ.get(m.group(1)), path)
        return path
