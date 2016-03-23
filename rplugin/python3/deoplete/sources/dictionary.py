# ============================================================================
# FILE: dictionary.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from os.path import getmtime, exists
from collections import namedtuple
from deoplete.util import parse_file_pattern
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
                    new_candidates = parse_file_pattern(
                        f, context['keyword_patterns'])
                    candidates += new_candidates
                self.__cache[filename] = DictCacheItem(
                    mtime, new_candidates)
            else:
                candidates += self.__cache[filename].candidates
        return [{'word': x} for x in candidates]


def get_dictionaries(vim, filetype):
    return vim.current.buffer.options.get('dictionary', '').split(',')
