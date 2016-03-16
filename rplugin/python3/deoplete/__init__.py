# ============================================================================
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
# ============================================================================

import neovim

from deoplete.deoplete import Deoplete


@neovim.plugin
class DeopleteHandlers(object):

    def __init__(self, vim):
        self.__vim = vim

    @neovim.function('_deoplete', sync=True)
    def init_python(self, args):
        self.__deoplete = Deoplete(self.__vim)
        self.__vim.vars['deoplete#_channel_id'] = self.__vim.channel_id

    @neovim.rpc_export('deoplete_auto_completion_begin')
    def completion_begin(self, context):
        context['rpc'] = 'deoplete_auto_completion_begin'
        self.__deoplete.completion_begin(context)

    @neovim.rpc_export('deoplete_manual_completion_begin', sync=True)
    def manual_completion_begin(self, context):
        context['rpc'] = 'deoplete_manual_completion_begin'
        self.__deoplete.completion_begin(context)
