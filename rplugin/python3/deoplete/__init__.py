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
from .deoplete import Deoplete

@neovim.plugin
class DeopleteHandlers(object):
    def __init__(self, vim):
        self.vim = vim

    def debug(self, msg):
        self.vim.command('echomsg string("' + str(msg) + '")')

    @neovim.command('DeopleteInitializePython', sync=True, nargs=0)
    def init_python(self):
        self.deoplete = Deoplete(self.vim)
        self.vim.command('let g:deoplete#_channel_id = '
        + str(self.vim.channel_id))

    @neovim.rpc_export('completion_begin')
    def completion_begin(self, context):
        # Encoding conversion
        encoding = self.vim.eval('&encoding')
        context = { k.decode(encoding) :
                    (v.decode(encoding) if isinstance(v, bytes) else v)
                    for k, v in context.items()}

        # Call omni completion
        omni_pattern = self.vim.eval(
            'deoplete#util#get_buffer_config('\
            +'"b:deoplete#omni_pattern", deoplete#omni_patterns,'\
            +'g:deoplete#_omni_patterns)')
        # self.debug(omni_pattern)
        if omni_pattern != '' \
                and re.search('('+omni_pattern+')$', context['input']) \
                and self.vim.eval('mode()') == 'i':
            self.vim.command(
                'call feedkeys("\<C-x>\<C-o>", "n")')

        candidates = self.deoplete.gather_candidates(context)
        if not candidates or self.vim.eval('mode()') != 'i':
                return
        self.vim.command(
          'let g:deoplete#_context = {}')
        self.vim.command(
          'let g:deoplete#_context.complete_position = 0')
        self.vim.command(
          'let g:deoplete#_context.changedtick = '
            + str(context['changedtick']))
        self.vim.command(
          'let g:deoplete#_context.candidates = ' + str(candidates))
        self.vim.command(
          'call feedkeys("\<Plug>(deoplete_start_complete)")')

