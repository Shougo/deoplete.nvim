# ============================================================================
# FILE: tag.py
# AUTHOR: Felipe Morales <hel.sheep at gmail.com>
#         Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from .base import Base

from collections import namedtuple
from os.path import exists, getmtime, getsize
from deoplete.util import parse_file_pattern

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
        tagfiles = self.__make_cache(context)

        candidates = []
        for filename in [x for x in tagfiles if x in self.__cache]:
            candidates.append(self.__cache[filename].candidates)
        return {'sorted_candidates': candidates}

    def __make_cache(self, context):
        tagfiles = self.__get_tagfiles(context)

        for filename in tagfiles:
            mtime = getmtime(filename)
            if filename in self.__cache and self.__cache[
                    filename].mtime == mtime:
                continue
            with open(filename, 'r', errors='replace') as f:
                self.__cache[filename] = TagsCacheItem(
                    mtime, [{'word': x} for x in sorted(
                        parse_file_pattern(f, '^[^!][^\t]+'), key=str.lower)]
                )
        return tagfiles

    def __get_tagfiles(self, context):
        include_files = self.vim.call(
            'neoinclude#include#get_tag_files') if self.vim.call(
                'exists', '*neoinclude#include#get_tag_files') else []
        return [x for x in self.vim.call(
                'map', self.vim.call('tagfiles') + include_files,
                'fnamemodify(v:val, ":p")')
                if exists(x) and getsize(x) < self.__limit]
