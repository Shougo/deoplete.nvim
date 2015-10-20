#=============================================================================
# FILE: __init__.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license  {{{
#     Permission is hereby granted, free of charge, to any person obtaining
#     a copy of this software and associated documentation files (the
#     "Software"), to deal in the Software without restriction, including
#     without limitation the rights to use, copy, modify, merge, publish,
#     distribute, sublicense, and/or sell copies of the Software, and to
#     permit persons to whom the Software is furnished to do so, subject to
#     the following conditions:
#
#     The above copyright notice and this permission notice shall be included
#     in all copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#     OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#     MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#     IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#     CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#     TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#     SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# }}}
#=============================================================================

import neovim
import re
import traceback

import deoplete
from deoplete.deoplete import Deoplete
from deoplete.util import \
    debug, error, convert2list, get_buffer_config

@neovim.plugin
class DeopleteHandlers(object):
    def __init__(self, vim):
        self.vim = vim

    @neovim.command('DeopleteInitializePython', sync=True, nargs=0)
    def init_python(self):
        self.deoplete = Deoplete(self.vim)
        self.vim.vars['deoplete#_channel_id'] = self.vim.channel_id

    @neovim.rpc_export('completion_begin')
    def completion_begin(self, context):
        # Skip
        if self.vim.eval('g:deoplete#_skip_next_complete'):
            self.vim.vars['deoplete#_skip_next_complete'] = 0
            return
        if self.vim.eval('&paste') != 0:
            return
        if context['position'] == self.vim.eval(
                'get(g:deoplete#_context, "position", [])'):
            return

        var_context = {}

        # Save previous position
        var_context['position'] = context['position']

        # Call omni completion
        omni_patterns = convert2list(get_buffer_config(
            self.vim, context,
            'b:deoplete_omni_patterns',
            'g:deoplete#omni_patterns',
            'g:deoplete#_omni_patterns'))
        # debug(self.vim, omni_patterns)
        for pattern in omni_patterns:
            if self.vim.eval('mode()') == 'i' \
                    and (pattern != ''
                         and self.vim.eval('&l:omnifunc') != ''
                         and re.search('('+pattern+')$', context['input'])) \
                         or self.vim.eval(
                             'deoplete#util#is_eskk_convertion()') != 0:
                self.vim.command(
                    'call feedkeys("\<C-x>\<C-o>", "n")')
                self.vim.vars['deoplete#_context'] = var_context
                return

        try:
            complete_position, candidates = self.deoplete.gather_candidates(
                context)
        except Exception as e:
            for line in traceback.format_exc().splitlines():
                 error(self.vim, line)
            error(self.vim,
                  'An error has occurred. Please execute :messages command.')
            candidates = []

        if not candidates or self.vim.eval('mode()') != 'i':
            self.vim.vars['deoplete#_context'] = var_context
            return

        # debug(self.vim, candidates)
        var_context['complete_position'] = complete_position
        var_context['changedtick'] = context['changedtick']
        var_context['candidates'] = candidates
        self.vim.vars['deoplete#_context'] = var_context

        self.vim.command(
          'call feedkeys("\<Plug>(deoplete_start_complete)")')

