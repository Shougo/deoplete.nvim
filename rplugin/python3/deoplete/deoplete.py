# ============================================================================
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
# ============================================================================

from deoplete.util import \
    globruntime, get_simple_buffer_config, charpos2bytepos, \
    bytepos2charpos, get_custom, get_buffer_config

import deoplete.sources
import deoplete.filters
import deoplete.util

import re
import importlib.machinery
import os.path
import copy

deoplete.sources  # silence pyflakes
deoplete.filters  # silence pyflakes


class Deoplete(object):

    def __init__(self, vim):
        self.vim = vim
        self.filters = {}
        self.sources = {}
        self.runtimepath = ''

    def debug(self, expr):
        deoplete.util.debug(self.vim, expr)

    def load_sources(self):
        # Load sources from runtimepath
        for path in globruntime(self.vim,
                                'rplugin/python3/deoplete/sources/base.py'
                                ) + globruntime(
                                    self.vim,
                                    'rplugin/python3/deoplete/sources/*.py'):
            name = os.path.basename(path)[: -3]
            source = importlib.machinery.SourceFileLoader(
                'deoplete.sources.' + name, path).load_module()
            if hasattr(source, 'Source') and name not in self.sources:
                self.sources[name] = source.Source(self.vim)
        # self.debug(self.sources)

    def load_filters(self):
        # Load filters from runtimepath
        for path in globruntime(self.vim,
                                'rplugin/python3/deoplete/filters/base.py'
                                ) + globruntime(
                                    self.vim,
                                    'rplugin/python3/deoplete/filters/*.py'):
            name = os.path.basename(path)[: -3]
            filter = importlib.machinery.SourceFileLoader(
                'deoplete.filters.' + name, path).load_module()
            if hasattr(filter, 'Filter') and name not in self.filters:
                self.filters[name] = filter.Filter(self.vim)
        # self.debug(self.filters)

    def gather_candidates(self, context):
        # Skip completion
        if (self.vim.eval('&l:completefunc') != '' and
                'nofile' in self.vim.eval('&l:buftype')
            ) or (context['event'] != 'Manual' and
                  get_simple_buffer_config(
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

        results = self.gather_results(context)
        return self.merge_results(results)

    def gather_results(self, context):
        # sources = ['buffer', 'neosnippet']
        # sources = ['buffer']
        sources = sorted(self.sources.items(),
                         key=lambda x: get_custom(self.vim, x[1].name).get(
                             'rank', x[1].rank),
                         reverse=True)
        results = []
        start_length = self.vim.eval(
            'g:deoplete#auto_completion_start_length')
        ignore_sources = get_buffer_config(
            self.vim, context,
            'b:deoplete_ignore_sources',
            'g:deoplete#ignore_sources',
            '{}')
        for source_name, source in sources:
            in_sources = not context['sources'] or (
                source_name in context['sources'])
            in_fts = not source.filetypes or (
                context['filetype'] in source.filetypes)
            in_ignore = source_name in ignore_sources
            if not in_sources or not in_fts or in_ignore:
                continue
            cont = copy.deepcopy(context)
            charpos = source.get_complete_position(cont)
            if charpos >= 0 and source.is_bytepos:
                charpos = bytepos2charpos(
                    self.vim, cont['input'], charpos)
            cont['complete_str'] = cont['input'][charpos:]
            cont['complete_position'] = charpos2bytepos(
                self.vim, cont['input'], charpos)
            # self.debug(source.rank)
            # self.debug(source_name)
            # self.debug(cont['input'])
            # self.debug(charpos)
            # self.debug(cont['complete_position'])
            # self.debug(cont['complete_str'])

            min_pattern_length = get_custom(self.vim, source.name).get(
                'min_pattern_length', source.min_pattern_length)
            if min_pattern_length < 0:
                # Use default value
                min_pattern_length = start_length

            if charpos < 0 or (cont['event'] != 'Manual' and
                               len(cont['complete_str']) <
                               min_pattern_length):
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

            # self.debug(source.name)
            context['candidates'] = source.gather_candidates(context)
            if context['candidates'] and isinstance(
                    context['candidates'][0], str):
                # Convert to dict
                context['candidates'] = [{'word': x}
                                         for x in context['candidates']]

            matchers = get_custom(self.vim, source.name).get(
                'matchers', source.matchers)
            sorters = get_custom(self.vim, source.name).get(
                'sorters', source.sorters)
            converters = get_custom(self.vim, source.name).get(
                'converters', source.converters)

            ignorecase = context['ignorecase']
            try:
                # Set ignorecase
                if context['smartcase'] and re.match(r'[A-Z]',
                                                     context['complete_str']):
                    context['ignorecase'] = 0

                for filter_name in matchers + sorters + converters:
                    if filter_name in self.filters:
                        context['candidates'] = self.filters[
                            filter_name].filter(context)
            finally:
                context['ignorecase'] = ignorecase
            # self.debug(context['candidates'])

            # On post filter
            if hasattr(source, 'on_post_filter'):
                context['candidates'] = source.on_post_filter(context)

            if context['candidates'] and (
                    not re.match(r'\[.*\]',
                                 context['candidates'][0].get('menu', ''))):
                # Set default menu
                for candidate in context['candidates']:
                    candidate['menu'] = source.mark + ' ' + candidate.get(
                        'menu', '')

            # Set icase
            for candidate in context['candidates']:
                candidate['icase'] = 1
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
            prefix = context['input'][context[
                'complete_position'] - complete_position:]

            context['complete_position'] = complete_position
            context['complete_str'] = prefix

            # Add prefix
            for candidate in context['candidates']:
                candidate['word'] = prefix + candidate['word']
            candidates += context['candidates']
        # self.debug(candidates)
        return (complete_position, candidates)
