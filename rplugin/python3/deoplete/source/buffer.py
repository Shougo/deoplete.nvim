# ============================================================================
# FILE: buffer.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from deoplete.source.base import Base
from deoplete.util import parse_buffer_pattern, getlines


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'buffer'
        self.mark = '[B]'
        self.events = ['Init', 'BufReadPost', 'BufWritePost', 'BufDelete']
        self.vars = {
            'require_same_filetype': True,
        }

        self._limit = 1000000
        self._buffers = {}
        self._max_lines = 5000

    def on_event(self, context):
        if context['event'] == 'BufDelete':
            # Remove deleted buffer cache
            if context['bufnr'] in self._buffers:
                self._buffers.pop(context['bufnr'])
        else:
            self._make_cache(context)

    def gather_candidates(self, context):
        tab_bufnrs = self.vim.call('tabpagebuflist')
        same_filetype = self.get_var('require_same_filetype')
        return {'sorted_candidates': [
            x['candidates'] for x in self._buffers.values()
            if not same_filetype or
            x['filetype'] in context['filetypes'] or
            x['filetype'] in context['same_filetypes'] or
            x['bufnr'] in tab_bufnrs
        ]}

    def _make_cache(self, context):
        # Bufsize check
        size = self.vim.call('line2byte',
                             self.vim.call('line', '$') + 1) - 1
        if size > self._limit:
            return

        try:
            self._buffers[context['bufnr']] = {
                'bufnr': context['bufnr'],
                'filetype': self.vim.eval('&l:filetype'),
                'candidates': [
                    {'word': x} for x in
                    sorted(parse_buffer_pattern(getlines(self.vim),
                                                context['keyword_pattern']),
                           key=str.lower)
                ]
            }
        except UnicodeDecodeError:
            return []
