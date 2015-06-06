#=============================================================================
# FILE: deoplete.py
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
import importlib
from .sources.buffer import Buffer
# from .filters.matcher_head import Filter
from .filters.matcher_fuzzy import Filter

class Deoplete(object):
    def __init__(self, base_dir):
        self.base_dir = base_dir
    def gather_candidates(self, vim, context):
        # Skip completion
        if vim.eval('&l:completefunc') != '' \
          and vim.eval('&l:buftype').find('nofile') >= 0:
            return []

        # Encoding conversion
        encoding = vim.eval('&encoding')
        context = { k.decode(encoding) :
                    (v.decode(encoding) if isinstance(v, bytes) else v)
                    for k, v in context.items()}
        # debug(vim, context)

        if context['complete_str'] == '':
            return []

        buffer = Buffer()
        context['candidates'] = buffer.gather_candidates(vim, context)

        # Set ignorecase
        if context['smartcase'] \
                and re.search(r'[A-Z]', context['complete_str']):
            context['ignorecase'] = 0

        filter = Filter()
        context['candidates'] = filter.filter(vim, context)
        return context['candidates']

def debug(vim, msg):
        vim.command('echomsg string(' + str(msg) + ')')
