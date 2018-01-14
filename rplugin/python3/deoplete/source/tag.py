# ============================================================================
# FILE: tag.py
# AUTHOR: Felipe Morales <hel.sheep at gmail.com>
#         Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re

from .base import Base

from collections import namedtuple
from os.path import exists, getmtime, getsize

TagsCacheItem = namedtuple('TagsCacheItem', 'mtime candidates')


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'tag'
        self.mark = '[T]'

        self.__cache = {}

    def on_init(self, context):
        self.__limit = context['vars'].get(
            'deoplete#tag#cache_limit_size', 500000)

    def on_event(self, context):
        self.__make_cache(context)

    def gather_candidates(self, context):
        self.__make_cache(context)
        candidates = []
        for c in self.__cache.values():
            candidates.extend(c.candidates)
        return candidates

    def __make_cache(self, context):
        for filename in self.__get_tagfiles(context):
            mtime = getmtime(filename)
            if filename in self.__cache and self.__cache[
                    filename].mtime == mtime:
                continue

            items = []

            with open(filename, 'r', errors='replace') as f:
                for line in f:
                    cols = line.strip().split('\t')
                    if not cols or cols[0].startswith('!_'):
                        continue
                    i = cols[2].find('(')
                    if i != -1 and cols[2].find(')', i+1) != -1:
                        m = re.search(r'(\w+\(.*\))', cols[2])
                        if m:
                            items.append({'word': cols[0],
                                          'abbr': m.group(1),
                                          'kind': 'f'})
                            continue
                    items.append({'word': cols[0]})

            if not items:
                continue

            self.__cache[filename] = TagsCacheItem(
                mtime, sorted(items, key=lambda x: x['word'].lower()))

    def __get_tagfiles(self, context):
        include_files = self.vim.call(
            'neoinclude#include#get_tag_files') if self.vim.call(
                'exists', '*neoinclude#include#get_tag_files') else []
        return [x for x in self.vim.call(
                'map', self.vim.call('tagfiles') + include_files,
                'fnamemodify(v:val, ":p")')
                if exists(x) and getsize(x) < self.__limit]
