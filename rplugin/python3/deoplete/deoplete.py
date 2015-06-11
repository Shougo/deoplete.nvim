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
import importlib.machinery
import os.path
import deoplete.sources
import deoplete.filters

class Deoplete(object):
    def __init__(self, vim):
        self.vim = vim
        self.filters = {}
        self.sources = {}

        # Load sources from runtimepath
        for path in self.vim.eval(
                "globpath(&runtimepath, \
                'rplugin/python3/deoplete/sources/*.py')").split("\n"):
            name = os.path.basename(path)
            source = importlib.machinery.SourceFileLoader(
                'deoplete.sources.' + name[: -3], path).load_module()
            if hasattr(source, 'Source'):
                 self.sources[name] = source.Source()
        # self.debug(self.sources)

        # Load filters from runtimepath
        for path in self.vim.eval(
                "globpath(&runtimepath, \
                'rplugin/python3/deoplete/filters/*.py')").split("\n"):
            name = os.path.basename(path)
            filter = importlib.machinery.SourceFileLoader(
                'deoplete.filters.' + name[: -3], path).load_module()
            if hasattr(filter, 'Filter'):
                 self.filters[name] = filter.Filter()
        # self.debug(self.filters)

    def debug(self, msg):
        self.vim.command('echomsg string("' + str(msg) + '")')

    def gather_candidates(self, vim, context):
        # Skip completion
        if self.vim.eval('&l:completefunc') != '' \
          and self.vim.eval('&l:buftype').find('nofile') >= 0:
            return []

        # Encoding conversion
        encoding = self.vim.eval('&encoding')
        context = { k.decode(encoding) :
                    (v.decode(encoding) if isinstance(v, bytes) else v)
                    for k, v in context.items()}
        # self.debug(context)

        if context['complete_str'] == '':
            return []

        # Set ignorecase
        if context['smartcase'] \
                and re.search(r'[A-Z]', context['complete_str']):
            context['ignorecase'] = 0

        sources = ['buffer', 'neosnippet']
        candidates = []
        for source_name in sources:
            key = source_name + '.py'
            if not key in self.sources:
                continue

            source = self.sources[key]
            context['candidates'] = source.gather_candidates(
                self.vim, context)

            for filter_name in source.filters:
                key = filter_name + '.py'
                if key in self.filters:
                    context['candidates'] = self.filters[key].filter(
                        self.vim, context)
            # self.debug(context['candidates'])
            candidates += context['candidates']

        return candidates

