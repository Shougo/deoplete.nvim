# ============================================================================
# FILE: tag.py
# AUTHOR: Felipe Morales <hel.sheep at gmail.com>
#         Shougo Matsushita <Shougo.Matsu at gmail.com>
#         Roxma <roxma at qq.com>
# License: MIT license
# ============================================================================

import re
import os
from os.path import exists

from deoplete.source.base import Base


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'tag'
        self.mark = '[T]'

    def gather_candidates(self, context):
        candidates = []

        case = context['smartcase'] or context['camelcase']
        ignorecase = context['ignorecase']
        if case and re.search(r'[A-Z]', context['complete_str']):
            ignorecase = True
        if ignorecase:
            complete_str_0 = (context['complete_str'][0].lower()
                              if len(context['complete_str']) > 0 else '')
            complete_str_1 = (context['complete_str'][1].lower()
                              if len(context['complete_str']) > 1 else '')
            prefixes = list({
                complete_str_0 + complete_str_1,
                complete_str_0 + complete_str_1.upper(),
                complete_str_0.upper() + complete_str_1,
                complete_str_0.upper() + complete_str_1.upper(),
                })
        else:
            prefixes = [context['complete_str']]

        for filename in self._get_tagfiles(context):
            for prefix in [x for x in prefixes if x]:
                for line in binary_search_lines_by_prefix(prefix, filename):
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
                'fnamemodify(v:val, ":p")') if exists(x)]


def binary_search_lines_by_prefix(prefix, filename):

    with open(filename, 'r', errors='ignore') as f:
        # to properly keep bounds of this loop it's important to understand
        # *exactly* what our variables mean.
        #
        # to make sure we process only full lines, we are going to always seek
        # to file position (x - 1), then skip partial or full line found there.
        # except for position 0 which we know belongs to full 1st line.

        # each line (except 1st one) will have multiple corresponding seeking
        # positions.
        #
        # we are interested in finding such a seeking position for the first
        # line in the file that matches our prefix. (let's call it target)

        # begin - guaranteed not to exceed our target position
        # e.g. (begin <= target) at any time.
        begin = 0

        # end - guaranteed to be higher then at least one seeking position for
        # the target. e.g. (target < end) at any time.
        # Note that this means it can be below the actual target line
        f.seek(0, os.SEEK_END)
        end = f.tell()

        while end > begin + 1:

            # pos - current seeking position
            pos = int((begin + end) / 2) - 1

            if pos == 0:
                f.seek(0, os.SEEK_SET)
            else:
                f.seek(pos - 1, os.SEEK_SET)
                f.readline()  # skip partial line

            line = f.readline()

            l2 = f.tell()  # start of next line (or end of file)

            if l2 == 1:
                # this is a corner case of a single empty first line.
                # we mast advance here or we'll have an endless loop
                begin = 1
                next

            if line:
                key = line[:len(prefix)]

                if key < prefix:
                    # we are strictly before the target line.
                    # so it starts at least from l2
                    begin = max(begin, l2)

                elif key > prefix:
                    # we are strictly past the target line.
                    # our target seeking position is less than current pos
                    end = pos
                else:
                    # current line is a possible target.  it's reachable from
                    # current 'pos', so `target pos is <= current pos`, or
                    # `target post < current post + 1`
                    end = min(end, pos + 1)

            else:
                # we reached end of file. our current seeking position doesn't
                # correspond to any line
                end = min(end, pos)

        # now we are at a *seeking position* for the target line. need to skip
        # to the actual line
        if begin == 0:
            f.seek(0, os.SEEK_SET)
        else:
            f.seek(begin - 1, os.SEEK_SET)
            f.readline()

        while True:
            line = f.readline()
            if line.startswith(prefix):
                yield line
            else:
                break
        return
