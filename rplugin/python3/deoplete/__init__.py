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
from .deoplete import Deoplete

@neovim.plugin
class DeopleteHandlers(object):
    def __init__(self, vim):
        self.vim = vim

    @neovim.command('DeopleteInitializePython', sync=True, nargs=1)
    def init_python(self, base_dir):
        self.deoplete = Deoplete(base_dir, self.vim)
        self.vim.command('let g:deoplete#_channel_id = '
        + str(self.vim.channel_id))

    @neovim.rpc_export('completion_begin')
    def completion_begin(self, context):
        candidates = self.deoplete.gather_candidates(self.vim, context)
        if not candidates or self.vim.eval('mode()') != 'i':
                return
        self.vim.command(
          'let g:deoplete#_context = {}')
        self.vim.command(
          'let g:deoplete#_context.complete_position = 0')
        self.vim.command(
          'let g:deoplete#_context.changedtick = '
            + str(context[b'changedtick']))
        self.vim.command(
          'let g:deoplete#_context.candidates = ' + str(candidates))
        self.vim.command(
          'call feedkeys("\<Plug>(deoplete_start_auto_complete)")')

