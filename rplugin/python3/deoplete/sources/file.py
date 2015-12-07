# ============================================================================
# FILE: file.py
# AUTHOR: Felipe Morales <hel.sheep at gmail.com>
#         Shougo Matsushita <Shougo.Matsu at gmail.com>
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

import os
import re
from os.path import exists, dirname
from .base import Base


def longest_path_that_exists(vim, input_str):
    data = input_str.split(' ')
    pos = [" ".join(data[i:]) for i in range(len(data))]
    existing_paths = list(filter(lambda x: exists(
        dirname(substitute_path(vim, x))), pos))
    if existing_paths and len(existing_paths) > 0:
        return sorted(existing_paths)[-1]
    return None


def substitute_path(vim, path):
    m = re.match(r'[.~]/', path)
    if m:
        return re.sub(r'^[.~]', vim.funcs.getcwd(), path)
    m = re.match(r'\$([A-Z_]+)/', path)
    if m and os.environ.get(m.group(1)):
        return re.sub(r'^\$[A-Z_]+', os.environ.get(m.group(1)), path)
    return path


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'file'
        self.mark = '[F]'
        self.min_pattern_length = 0

    def get_complete_position(self, context):
        pos = context['input'].rfind('/')
        return pos if pos < 0 else pos + 1

    def gather_candidates(self, context):
        p = longest_path_that_exists(self.vim, context['input'])
        if p in (None, []) or p == '/' or re.search('//+$', p):
            return []
        complete_str = substitute_path(self.vim, dirname(p) + '/')
        if not os.path.isdir(complete_str):
            return []
        hidden = context['complete_str'].find('.') == 0
        dirs = [x for x in os.listdir(complete_str)
                if os.path.isdir(complete_str + x)
                and (hidden or x[0] != '.')]
        files = [x for x in os.listdir(complete_str)
                 if not os.path.isdir(complete_str + x)
                 and (hidden or x[0] != '.')]
        return [{'word': x, 'abbr': x + '/'} for x in sorted(dirs)
                ] + [{'word': x} for x in sorted(files)]
