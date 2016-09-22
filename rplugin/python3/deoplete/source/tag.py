# ============================================================================
# FILE: tag.py
# AUTHOR: Felipe Morales <hel.sheep at gmail.com>
#         Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from .base import Base

import re
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
        self.__tagfiles = {}

    def on_init(self, context):
        self.__limit = context['vars'].get(
            'deoplete#tag#cache_limit_size', 500000)

    def on_event(self, context):
        self.__tagfiles[context['bufnr']] = self.__get_tagfiles(context)

        # Make cache
        for filename in self.__tagfiles[context['bufnr']]:
            mtime = getmtime(filename)
            if filename not in self.__cache or self.__cache[
                    filename].mtime != mtime:
                with open(filename, 'r', errors='replace') as f:
                    self.__cache[filename] = TagsCacheItem(
                        mtime, parse_file_pattern(f, '^[^!][^\t]+'))

    def gather_candidates(self, context):
        candidates = []
        for filename in [
                x for x in self.__tagfiles.get(context['bufnr'], [])
                if x in self.__cache]:
            candidates += self.__cache[filename].candidates

        p = re.compile('(?:{})$'.format(context['keyword_patterns']))
        return [{'word': x} for x in candidates if p.match(x)]

    def __get_tagfiles(self, context):
        include_files = self.vim.call(
            'neoinclude#include#get_tag_files') if self.vim.call(
                'exists', '*neoinclude#include#get_tag_files') else []
        return [x for x in self.vim.call(
                'map', self.vim.call('tagfiles') + include_files,
                'fnamemodify(v:val, ":p")')
                if exists(x) and getsize(x) < self.__limit]
