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
import copy

import deoplete.sources
import deoplete.util
import deoplete.filters

class Deoplete(object):
    def __init__(self, vim):
        self.vim = vim
        self.filters = {}
        self.sources = {}
        self.runtimepath = ''

    def load_sources(self):
        # Load sources from runtimepath
        for path in deoplete.util.globruntime(self.vim,
                'rplugin/python3/deoplete/sources/base.py') \
                + deoplete.util.globruntime(self.vim,
                'rplugin/python3/deoplete/sources/*.py'):
            name = os.path.basename(path)
            source = importlib.machinery.SourceFileLoader(
                'deoplete.sources.' + name[: -3], path).load_module()
            if hasattr(source, 'Source'):
                self.sources[name[: -3]] = source.Source(self.vim)
        # self.debug(self.sources)

    def load_filters(self):
        # Load filters from runtimepath
        for path in deoplete.util.globruntime(self.vim,
                'rplugin/python3/deoplete/filters/base.py') \
                + deoplete.util.globruntime(self.vim,
                'rplugin/python3/deoplete/filters/*.py'):
            name = os.path.basename(path)
            filter = importlib.machinery.SourceFileLoader(
                'deoplete.filters.' + name[: -3], path).load_module()
            if hasattr(filter, 'Filter'):
                self.filters[name[: -3]] = filter.Filter(self.vim)
        # self.debug(self.filters)

    def debug(self, msg):
        self.vim.command('echomsg string("' + str(msg) + '")')

    def gather_candidates(self, context):
        # Skip completion
        if (self.vim.eval('&l:completefunc') != '' \
                and self.vim.eval('&l:buftype').find('nofile') >= 0) \
                or (context['event'] != 'Manual' and \
                    deoplete.util.get_simple_buffer_config(
                        self.vim,
                        'b:deoplete_disable_auto_complete',
                        'g:deoplete#disable_auto_complete')):
            return (-1, [])

        if self.vim.eval('&runtimepath') != self.runtimepath:
            # Recache
            self.load_sources()
            self.load_filters()
            self.runtimepath = self.vim.eval('&runtimepath')

        # self.debug(context)

        # Set ignorecase
        if context['smartcase'] \
                and re.search(r'[A-Z]', context['complete_str']):
            context['ignorecase'] = 0

        results = self.gather_results(context)
        return self.merge_results(results)

    def gather_results(self, context):
        # sources = ['buffer', 'neosnippet']
        # sources = ['buffer']
        sources = context['sources']
        results = []
        start_length = self.vim.eval(
            'g:deoplete#auto_completion_start_length')
        for source_name, source in self.sources.items():
            if (sources and not source_name in sources) \
                    or (source.filetypes and
                        not context['filetype'] in source.filetypes):
                continue
            cont = copy.deepcopy(context)
            cont['complete_position'] = source.get_complete_position(cont)
            cont['complete_str'] = \
                cont['input'][cont['complete_position'] :]
            # self.debug(source_name)
            # self.debug(cont['input'])
            # self.debug(cont['complete_position'])
            # self.debug(cont['complete_str'])

            min_pattern_length = source.min_pattern_length
            if min_pattern_length < 0:
                # Use default value
                min_pattern_length = start_length

            if cont['complete_position'] < 0 \
                    or (cont['event'] != 'Manual' \
                        and len(cont['complete_str']) < min_pattern_length):
                # Skip
                continue
            results.append({
                'name': source_name,
                'source': source,
                'context': cont,
            })

        for result in results:
            context = result['context']
            source = result['source']
            context['candidates'] = source.gather_candidates(context)
            # self.debug(context['candidates'])

            # self.debug(context['complete_str'])
            # self.debug(context['candidates'])
            for filter_name in \
                    source.matchers + source.sorters + source.converters:
                if filter_name in self.filters:
                    context['candidates'] = \
                        self.filters[filter_name].filter(context)
            # self.debug(context['candidates'])

            # On post filter
            if hasattr(source, 'on_post_filter'):
                context['candidates'] = source.on_post_filter(context)

            # Set default menu
            for candidate in context['candidates']:
                if not 'menu' in candidate:
                    candidate['menu'] = source.mark
            # self.debug(context['candidates'])
        return results

    def merge_results(self, results):
        results = [x for x in results if x['context']['candidates']]
        if not results:
            return (-1, [])

        complete_position = min(
            [x['context']['complete_position'] for x in results])

        candidates = []
        for result in results:
            context = result['context']
            if context['complete_position'] <= complete_position:
                complete_position = context['complete_position']
                candidates += context['candidates']
                continue
            prefix = context['input']\
                [: context['complete_position'] - complete_position]

            context['complete_position'] = complete_position
            context['complete_str'] = prefix

            # Add prefix
            for candidate in context['candidates']:
                candidate['word'] = prefix + candidate['word']
            candidates += context['candidates']
        return (complete_position, candidates)

