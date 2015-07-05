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
import deoplete.util

@neovim.plugin
class DeopleteHandlers(object):
    def __init__(self, vim):
        self.vim = vim
        self.msgfile = self.vim.eval('tempname()')

    def debug(self, msg):
        self.vim.command('echomsg string("' + str(msg) + '")')

    def error(self, e):
        with open(self.msgfile, 'a') as f:
            traceback.print_exc(None, f)
        self.vim.command('call deoplete#util#print_error('
                         + '"The error is occurred.  Please read ".'
                         + 'string("'+self.msgfile+'").'
                         +'" file or execute :DeopleteMessages command.")')

    @neovim.command('DeopleteInitializePython', sync=True, nargs=0)
    def init_python(self):
        self.deoplete = Deoplete(self.vim)
        self.vim.command('let g:deoplete#_channel_id = '
        + str(self.vim.channel_id))

    @neovim.command('DeopleteMessages', sync=True, nargs=0)
    def print_error(self):
        self.vim.command('edit ' + self.msgfile)

    @neovim.rpc_export('completion_begin')
    def completion_begin(self, context):
        # Encoding conversion
        encoding = self.vim.eval('&encoding')
        context = { k.decode(encoding) :
                    (v.decode(encoding) if isinstance(v, bytes) else v)
                    for k, v in context.items()}

        # Call omni completion
        omni_patterns = deoplete.util.convert2list(
            deoplete.util.get_buffer_config(
                self.vim, context,
                'b:deoplete_omni_patterns',
                'g:deoplete#omni_patterns',
                'g:deoplete#_omni_patterns'))
        # self.debug(omni_pattern)
        for pattern in omni_patterns:
            if pattern != '' \
                    and self.vim.eval('&l:omnifunc') != '' \
                    and re.search('('+pattern+')$', context['input']) \
                    and self.vim.eval('mode()') == 'i':
                self.vim.command(
                    'call feedkeys("\<C-x>\<C-o>", "n")')
                return

        try:
            complete_position, candidates = \
                self.deoplete.gather_candidates(context)
        except Exception as e:
            self.error(e)
            candidates = []
        if not candidates or self.vim.eval('mode()') != 'i':
                return
        self.vim.command(
          'let g:deoplete#_context = {}')
        self.vim.command(
          'let g:deoplete#_context.complete_position = '
            + str(complete_position))
        self.vim.command(
          'let g:deoplete#_context.changedtick = '
            + str(context['changedtick']))
        self.vim.command(
          'let g:deoplete#_context.candidates = '
            + str(candidates))
        self.vim.command(
          'call feedkeys("\<Plug>(deoplete_start_complete)")')

