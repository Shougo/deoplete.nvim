# ============================================================================
# FILE: context.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import os
import re


class Context(object):

    def __init__(self, vim):
        self._vim = vim
        self._prev_filetype = self._vim.current.buffer.options['filetype']
        self._cached = None
        self._cached_filetype = self._init_cached_filetype(
            self._prev_filetype)
        self._init_cached()
        self._context_filetype = {}

    def get(self, event):
        text = self._vim.call('deoplete#util#get_input', event)
        [filetype, filetypes, same_filetypes] = self._get_context_filetype(
            text, event)

        m = re.search(r'\w$', text)
        word_len = len(m.group(0)) if m else 0
        width = self._vim.call('winwidth', 0) - self._vim.call('col', '.')
        width += word_len
        max_width = (width * 2 / 3)

        context = {
            'changedtick': self._vim.current.buffer.vars.get(
                'changedtick', 0),
            'event': event,
            'filetype': filetype,
            'filetypes': filetypes,
            'input': text,
            'max_abbr_width': max_width,
            'max_kind_width': max_width,
            'max_menu_width': max_width,
            'next_input': self._vim.call(
                'deoplete#util#get_next_input', event),
            'position': self._vim.call('getpos', '.'),
            'same_filetypes': same_filetypes,
        }
        context.update(self._cached)

        if filetype != self._prev_filetype:
            self._prev_filetype = filetype
            self._cached_filetype = self._init_cached_filetype(filetype)

        context.update(self._cached_filetype)

        return context

    def _init_cached_filetype(self, filetype):
        return {
            'keyword_pattern': self._vim.call(
                'deoplete#util#get_keyword_pattern', filetype),
            'sources': self._vim.call(
                'deoplete#custom#_get_filetype_option',
                'sources', filetype, []),
        }

    def _init_cached(self):
        bufnr = self._vim.call('expand', '<abuf>')
        if not bufnr:
            bufnr = self._vim.current.buffer.number
        if not bufnr:
            bufnr = -1
            bufname = ''
        else:
            bufname = self._vim.call('bufname', bufnr)
        cwd = self._vim.call('getcwd')
        buftype = self._vim.current.buffer.options['buftype']
        bufpath = (bufname if os.path.isabs(bufname)
                   else os.path.join(cwd, bufname))
        if not os.path.exists(bufpath) or 'nofile' in buftype:
            bufpath = ''

        self._cached = {
            'bufnr': bufnr,
            'bufname': bufname,
            'bufpath': bufpath,
            'camelcase': self._vim.call(
                'deoplete#custom#_get_option', 'camel_case'),
            'complete_str': '',
            'custom': self._vim.call('deoplete#custom#_get'),
            'cwd': cwd,
            'encoding': self._vim.options['encoding'],
            'ignorecase': self._vim.call(
                'deoplete#custom#_get_option', 'ignore_case'),
            'is_windows': self._vim.call('has', 'win32'),
            'smartcase': self._vim.call(
                'deoplete#custom#_get_option', 'smart_case'),
            'vars': {x: y for x, y in self._vim.eval('g:').items()
                     if x.startswith('deoplete#') and
                     not x.startswith('deoplete#_')},
        }

    def _get_context_filetype(self, text, event):
        if not self._context_filetype and self._vim.call(
                'exists', '*context_filetype#get_filetype'):
            # Force context_filetype call
            self._vim.call('context_filetype#get_filetype')

        filetype = self._vim.current.buffer.options['filetype']
        linenr = self._vim.call('line', '.')
        bufnr = self._vim.call('bufnr', '%')

        if (not self._context_filetype or
                self._context_filetype['prev_filetype'] != filetype or
                self._context_filetype['line'] != linenr or
                self._context_filetype['bufnr'] != bufnr or
                re.sub(r'\w+$', '', self._context_filetype['input']) !=
                re.sub(r'\w+$', '', self._context_filetype['input']) or
                event == 'InsertEnter'):
            self._cache_context_filetype(text, filetype, linenr, bufnr)

        return [
            self._context_filetype['filetype'],
            self._context_filetype['filetypes'],
            self._context_filetype['same_filetypes']
        ]

    def _cache_context_filetype(self, text, filetype, linenr, bufnr):
        exists_context_filetype = self._vim.call(
            'exists', '*context_filetype#get_filetype')
        self._context_filetype = {
            'line': linenr,
            'bufnr': bufnr,
            'input': text,
            'prev_filetype': filetype,
            'filetype': (
                self._vim.call('context_filetype#get_filetype')
                if exists_context_filetype
                else (filetype if filetype else 'nothing')),
            'filetypes': (
                self._vim.call('context_filetype#get_filetypes')
                if exists_context_filetype
                else filetype.split('.')),
            'same_filetypes': (
                self._vim.call('context_filetype#get_same_filetypes')
                if exists_context_filetype else []),
        }
