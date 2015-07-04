#=============================================================================
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
#=============================================================================

import re
import os
from os.path import exists, dirname
from glob import glob
from .base import Base

def longest_path_that_exists(input_str):
    data = input_str.split(' ')
    pos = [" ".join(data[i:]) for i in range(len(data))]
    existing_paths = list(filter(lambda x: exists(dirname(x)), pos))
    if existing_paths and len(existing_paths) > 0:
        return sorted(existing_paths)[-1]
    return None

class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'file'
        self.mark = '[F]'

    def get_complete_position(self, context):
        p = longest_path_that_exists(context['input'])
        if p not in (None, []):
            return context['input'].find(p)
        return -1

    def gather_candidates(self, context):
        dirs = [x for x in glob(context['complete_str'] + '*')
                      if os.path.isdir(x)]
        files = [x for x in glob(context['complete_str'] + '*')
                      if not os.path.isdir(x)]
        return [{ 'word': x, 'abbr': x + '/' } for x in sorted(dirs)] \
             + [{ 'word': x } for x in sorted(files)]

