# ============================================================================
# FILE: dictionary.py
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
from os.path import getmtime, exists
from collections import namedtuple
from .base import Base

DictCacheItem = namedtuple('DictCacheItem', 'mtime candidates')


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'dictionary'
        self.mark = '[D]'

        self.__cache = {}

    def gather_candidates(self, context):
        candidates = []
        for filename in [x for x in get_dictionaries(
                self.vim, context['filetype']) if exists(x)]:
            mtime = getmtime(filename)
            if filename not in self.__cache or self.__cache[
                    filename].mtime != mtime:
                with open(filename, 'r', errors='replace') as f:
                    new_candidates = parse_dictionary(
                        f, context['keyword_patterns'])
                    candidates += new_candidates
                self.__cache[filename] = DictCacheItem(
                    mtime, new_candidates)
            else:
                candidates += self.__cache[filename].candidates
        return [{'word': x} for x in candidates]


def parse_dictionary(f, keyword_patterns):
    p = re.compile(keyword_patterns)
    candidates = []

    for l in f.readlines():
        candidates += p.findall(l)
    return list(set(candidates))


def get_dictionaries(vim, filetype):
    return vim.eval('&l:dictionary').split(',')
