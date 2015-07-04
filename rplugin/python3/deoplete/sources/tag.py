#=============================================================================
# FILE: tag.py
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
from os.path import getmtime
from collections import namedtuple
from .base import Base

TagsCacheItem = namedtuple('TagsCacheItem', 'mtime tags')

class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'tag'
        self.mark = '[T]'

        self.cache = {}

    def gather_candidates(self, context):
        candidates = []
        for tags_file in self.vim.eval(
                'map(tagfiles(), "fnamemodify(v:val, \\":p\\")")'):
            mtime = getmtime(tags_file)
            if tags_file not in self.cache or \
                    self.cache[tags_file].mtime != mtime:
                with open(tags_file, 'r', errors='replace') as f:
                    new_candidates = parse_tags(f)
                    candidates += new_candidates
                self.cache[tags_file] = TagsCacheItem(mtime, new_candidates)
            else:
                candidates += self.cache[tags_file].tags
        return [{ 'word': x } for x in candidates]

def parse_tags(f):
    p = re.compile('^[a-zA-Z_]\w*(?=\t)')
    candidates = []

    for l in f.readlines():
        candidates += p.findall(l)
    return list(set(candidates))

