# ============================================================================
# FILE: tag.py
# AUTHOR: Felipe Morales <hel.sheep at gmail.com>
#         Shougo Matsushita <Shougo.Matsu at gmail.com>
#         Roxma <roxma at qq.com>
# License: MIT license
# ============================================================================

from .base import Base

import re
import os
from os.path import exists, getsize


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'tag'
        self.mark = '[T]'

    def on_init(self, context):
        self._limit = context['vars'].get(
            'deoplete#tag#cache_limit_size', 500000)

    def gather_candidates(self, context):
        candidates = []
        for filename in self._get_tagfiles(context):
            for line in binary_search_lines_by_prefix(
                    context['complete_str'], filename):
                candidate = self._make_candidate(line)
                if candidate:
                    candidates.append(candidate)
        return candidates

    def _make_candidate(self, line):
        cols = line.strip().split('\t', 2)
        if not cols or cols[0].startswith('!_'):
            return {}

        tagfield = {}
        if ';"' in cols[-1]:
            cols[-1], fields = cols[-1].split(';"', 1)
            for pair in fields.split('\t'):
                if ':' not in pair:
                    tagfield['kind'] = pair
                else:
                    k, v = pair.split(':', 1)
                    tagfield[k] = v

        kind = tagfield.get('kind', '')
        if kind == 'f':
            i = cols[2].find('(')
            if i != -1 and cols[2].find(')', i+1) != -1:
                m = re.search(r'(\w+\(.*\))', cols[2])
                if m:
                    return {'word': cols[0], 'abbr': m.group(1), 'kind': kind}
        return {'word': cols[0], 'kind': kind}

    def _get_tagfiles(self, context):
        include_files = self.vim.call(
            'neoinclude#include#get_tag_files') if self.vim.call(
                'exists', '*neoinclude#include#get_tag_files') else []
        return [x for x in self.vim.call(
                'map', self.vim.call('tagfiles') + include_files,
                'fnamemodify(v:val, ":p")')
                if exists(x) and getsize(x) < self._limit]


# Based on cm_tags.py in nvim-completion-manager
def binary_search_lines_by_prefix(prefix, filename):

    with open(filename, 'r', errors='ignore') as f:

        def yield_results():
            while True:
                line = f.readline()
                if not line:
                    return
                if line.startswith(prefix):
                    yield line
                else:
                    return

        begin = 0
        # Seek to the end
        f.seek(0, os.SEEK_END)
        end = f.tell()

        while begin < end:
            middle_cursor = int((begin + end) / 2)

            f.seek(middle_cursor, os.SEEK_SET)
            f.readline()

            line1 = f.readline()

            line2pos = f.tell()
            line2 = f.readline()

            line2end = f.tell()

            key1 = '~~'
            # If f.readline() returns an empty string, the end of the file has
            # been reached
            if line1:
                key1 = line1[:len(prefix)]

            key2 = '~~'
            if line2:
                key2 = line2[:len(prefix)]

            if key1 >= prefix:
                if line2pos < end:
                    end = line2pos
                else:
                    # (begin) ... | line0 int((begin+end)/2) | line1 (end) |
                    # line2 |
                    #
                    # This assignment push the middle_cursor forward, it may
                    # also result in a case where begin==end
                    #
                    # Do not use end = line1pos, may results in infinite loop
                    end = int((begin + end) / 2)
                    if end == begin:
                        if key1 == prefix:
                            # Find success
                            # Seek to the start
                            f.seek(line2pos, os.SEEK_SET)
                            yield from yield_results()
                        return
            elif key2 == prefix:
                # Find success
                # key1 < prefix  && next line key2 == prefix
                # Seek to the start
                f.seek(line2pos, os.SEEK_SET)
                yield from yield_results()
                return
            elif key2 < prefix:
                begin = line2end
                # If begin==end, then exit the loop
            else:
                # key1 < prefix &&  next line key2 > prefix here, not found
                return
