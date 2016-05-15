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

    def on_event(self, context):
        self.__make_cache(context)

    def gather_candidates(self, context):
        self.__make_cache(context)

        candidates = []
        for filename in [x for x in self.__get_dictionaries()
                         if x in self.__cache]:
            candidates += self.__cache[filename].candidates

        return [{'word': x} for x in candidates]

    def __make_cache(self, context):
        for filename in self.__get_dictionaries():
            mtime = getmtime(filename)
            if filename not in self.__cache or self.__cache[
                    filename].mtime != mtime:
                with open(filename, 'r', errors='replace') as f:
                    self.__cache[filename] = DictCacheItem(
                        mtime, parse_file_pattern(
                            f, context['keyword_patterns']))

    def __get_dictionaries(self):
        return [x for x in
                self.vim.current.buffer.options.get(
                    'dictionary', '').split(',')
                if exists(x)]
