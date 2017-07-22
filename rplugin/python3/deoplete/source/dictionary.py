# ============================================================================
# FILE: dictionary.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from os.path import getmtime, exists
from collections import namedtuple
from .base import Base

DictCacheItem = namedtuple('DictCacheItem', 'mtime candidates')


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'dictionary'
        self.mark = '[D]'

        self.__cache = {}

    def on_event(self, context):
        self.__make_cache(context)

    def gather_candidates(self, context):
        self.__make_cache(context)

        candidates = []
        for filename in [x for x in self.__get_dictionaries(context)
                         if x in self.__cache]:
            candidates.append(self.__cache[filename].candidates)
        return {'sorted_candidates': candidates}

    def __make_cache(self, context):
        for filename in self.__get_dictionaries(context):
            mtime = getmtime(filename)
            if filename in self.__cache and self.__cache[
                    filename].mtime == mtime:
                continue
            with open(filename, 'r', errors='replace') as f:
                self.__cache[filename] = DictCacheItem(
                    mtime, [{'word': x} for x in sorted(
                        [x.strip() for x in f], key=str.lower)]
                )

    def __get_dictionaries(self, context):
        return [x for x in context['dict__dictionary'].split(',')
                if exists(x)]
