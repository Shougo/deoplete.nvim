# ============================================================================
# FILE: deoplete.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from deoplete.util import \
    error, globruntime, charpos2bytepos, \
    bytepos2charpos, get_custom, get_syn_name, get_buffer_config

import deoplete.sources
import deoplete.filters
import deoplete.util
from deoplete import logger

import re
import importlib.machinery
import os.path
import copy
import traceback
import time

deoplete.sources  # silence pyflakes
deoplete.filters  # silence pyflakes


class Deoplete(logger.LoggingMixin):

    def __init__(self, vim):
        self.__vim = vim
        self.__filters = {}
        self.__sources = {}
        self.__runtimepath = ''
        self.__profile_flag = None
        self.__profile_start = 0
        self.name = 'core'

    def completion_begin(self, context):
        pos = self.__vim.current.window.cursor

        if context['event'] != 'Manual' and context['delay'] > 0:
            time.sleep(context['delay'] / 1000.0)
            if self.position_has_changed(pos):
                return

        try:
            complete_position, candidates = self.gather_candidates(context)
        except Exception:
            for line in traceback.format_exc().splitlines():
                error(self.__vim, line)
            error(self.__vim,
                  'An error has occurred. Please execute :messages command.')
            candidates = []

        if not candidates or self.position_has_changed(pos):
            self.__vim.vars['deoplete#_context'] = {}
            return

        self.__vim.vars['deoplete#_context'] = {
            'complete_position': complete_position,
            'changedtick': context['changedtick'],
            'candidates': candidates,
            'event': context['event'],
        }

        if context['rpc'] != 'deoplete_manual_completion_begin':
            # Set (and store) current &completeopt setting.  This cannot be
            # done (currently) from the deoplete_start_complete mapping's
            # function.
            self.__vim.call('deoplete#mappings#_set_completeopt')

        # Note: cannot use vim.feedkeys()
        self.__vim.command(
            'call feedkeys("\<Plug>(deoplete_start_complete)")')

    def gather_candidates(self, context):
        self.check_recache()

        # self.debug(context)

        results = self.gather_results(context)
        return self.merge_results(results)

    def gather_results(self, context):
        # sources = ['buffer', 'neosnippet']
        # sources = ['buffer']
        results = []
        for source_name, source in self.itersource(context):
            if source.disabled_syntaxes and 'syntax_name' not in context:
                context['syntax_name'] = get_syn_name(self.__vim)
            cont = copy.deepcopy(context)
            charpos = source.get_complete_position(cont)
            if charpos >= 0 and source.is_bytepos:
                charpos = bytepos2charpos(
                    self.__vim, cont['input'], charpos)
            cont['complete_str'] = cont['input'][charpos:]
            cont['complete_position'] = charpos2bytepos(
                self.__vim, cont['input'], charpos)
            cont['max_abbr_width'] = min(source.max_abbr_width,
                                         cont['max_abbr_width'])
            cont['max_menu_width'] = min(source.max_menu_width,
                                         cont['max_menu_width'])
            if cont['max_abbr_width'] > 0:
                cont['max_abbr_width'] = max(20, cont['max_abbr_width'])
            if cont['max_menu_width'] > 0:
                cont['max_menu_width'] = max(10, cont['max_menu_width'])
            # self.debug(source.rank)
            # self.debug(source_name)
            # self.debug(cont['input'])
            # self.debug(charpos)
            # self.debug(cont['complete_position'])
            # self.debug(cont['complete_str'])

            if charpos < 0 or self.is_skip(cont, source.disabled_syntaxes,
                                           source.min_pattern_length,
                                           source.max_pattern_length,
                                           source.input_pattern):
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
            self.profile_start(source.name)
            context['candidates'] = source.gather_candidates(context)
            self.profile_end(source.name)
            if context['candidates'] and isinstance(
                    context['candidates'][0], str):
                # Convert to dict
                context['candidates'] = [{'word': x}
                                         for x in context['candidates']]

            ignorecase = context['ignorecase']
            smartcase = context['smartcase']
            camelcase = context['camelcase']
            try:
                # Set ignorecase
                if (smartcase or camelcase) and re.search(
                        r'[A-Z]', context['complete_str']):
                    context['ignorecase'] = 0

                for filter in [self.__filters[x] for x
                               in source.matchers +
                               source.sorters +
                               source.converters
                               if x in self.__filters]:
                    self.profile_start(filter.name)
                    context['candidates'] = filter.filter(context)
                    self.profile_end(filter.name)
            finally:
                context['ignorecase'] = ignorecase
            # self.debug(context['candidates'])

            # On post filter
            if hasattr(source, 'on_post_filter'):
                context['candidates'] = source.on_post_filter(context)

            candidates = context['candidates']
            if candidates and source.mark != '' and candidates[0].get(
                    'menu', '').find(source.mark) != 0:
                # Set default menu
                for candidate in candidates:
                    candidate['menu'] = source.mark + ' ' + candidate.get(
                        'menu', '')

            # self.debug(context['candidates'])
        return results

    def itersource(self, context):
        sources = sorted(self.__sources.items(),
                         key=lambda x: get_custom(self.__vim, x[1].name).get(
                             'rank', x[1].rank),
                         reverse=True)
        filetypes = context['filetypes']
        ignore_sources = set()
        for ft in filetypes:
            ignore_sources.update(
                get_buffer_config(self.__vim, ft,
                                  'b:deoplete_ignore_sources',
                                  'g:deoplete#ignore_sources',
                                  '{}'))

        for source_name, source in sources:
            if (source_name in ignore_sources):
                continue
            if context['sources'] and source_name not in context['sources']:
                continue
            if source.filetypes and not any(x in filetypes
                                            for x in source.filetypes):
                continue

            yield source_name, source

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
                candidates += context['candidates']
                continue
            prefix = context['input'][
                complete_position:context['complete_position']]

            context['complete_position'] = complete_position
            context['complete_str'] = prefix

            # Add prefix
            for candidate in context['candidates']:
                candidate['word'] = prefix + candidate['word']
            candidates += context['candidates']
        # self.debug(candidates)
        if self.__vim.vars['deoplete#max_list'] > 0:
            candidates = candidates[: self.__vim.vars['deoplete#max_list']]

        # Set icase
        for candidate in candidates:
            candidate['icase'] = 1
        return (complete_position, candidates)

    def profile_start(self, name):
        if self.__profile_flag is 0 or not self.debug_enabled:
            return

        if self.__profile_flag is None:
            self.__profile_flag = self.__vim.vars[
                'deoplete#enable_profile']
            if self.__profile_flag:
                return self.profile_start(name)
        elif self.__profile_flag:
            self.debug('Profile Start: {0}'.format(name))
            self.__profile_start = time.clock()

    def profile_end(self, name):
        if self.__profile_start:
            self.debug('Profile End  : {0:<25} time={1:2.10f}'.format(
                name, time.clock() - self.__profile_start))

    def load_sources(self):
        # Load sources from runtimepath
        for path in globruntime(self.__vim,
                                'rplugin/python3/deoplete/sources/base.py'
                                ) + globruntime(
                                    self.__vim,
                                    'rplugin/python3/deoplete/sources/*.py'):
            name = os.path.basename(path)[: -3]
            module = importlib.machinery.SourceFileLoader(
                'deoplete.sources.' + name, path).load_module()
            if not hasattr(module, 'Source') or name in self.__sources:
                continue

            source = module.Source(self.__vim)

            # Set the source attributes.
            source.filetypes = get_custom(
                self.__vim, source.name).get(
                    'filetypes', source.filetypes)
            source.disabled_syntaxes = get_custom(
                self.__vim, source.name).get(
                    'disabled_syntaxes', source.disabled_syntaxes)
            source.input_pattern = get_custom(
                self.__vim, source.name).get(
                    'input_pattern', source.input_pattern)
            source.min_pattern_length = get_custom(
                self.__vim, source.name).get(
                    'min_pattern_length', source.min_pattern_length)
            source.max_pattern_length = get_custom(
                self.__vim, source.name).get(
                    'max_pattern_length', source.max_pattern_length)
            source.max_abbr_width = get_custom(
                self.__vim, source.name).get(
                    'max_abbr_width', source.max_abbr_width)
            source.max_menu_width = get_custom(
                self.__vim, source.name).get(
                    'max_menu_width', source.max_menu_width)
            source.matchers = get_custom(
                self.__vim, source.name).get('matchers', source.matchers)
            source.sorters = get_custom(self.__vim, source.name).get(
                'sorters', source.sorters)
            source.converters = get_custom(self.__vim, source.name).get(
                'converters', source.converters)
            source.mark = get_custom(self.__vim, source.name).get(
                'mark', source.mark)

            self.__sources[source.name] = source
            self.debug('Loaded Source: %s (%s)', name, module.__file__)
        # self.debug(self.__sources)

    def load_filters(self):
        # Load filters from runtimepath
        for path in globruntime(self.__vim,
                                'rplugin/python3/deoplete/filters/base.py'
                                ) + globruntime(
                                    self.__vim,
                                    'rplugin/python3/deoplete/filters/*.py'):
            name = os.path.basename(path)[: -3]
            module = importlib.machinery.SourceFileLoader(
                'deoplete.filters.' + name, path).load_module()
            if hasattr(module, 'Filter') and name not in self.__filters:
                filter = module.Filter(self.__vim)
                self.__filters[filter.name] = filter
                self.debug('Loaded Filter: %s (%s)', name, module.__file__)
        # self.debug(self.__filters)

    def is_skip(self, context, disabled_syntaxes,
                min_pattern_length, max_pattern_length, input_pattern):
        if ('syntax_name' in context and
                context['syntax_name'] in disabled_syntaxes):
            return 1
        if (input_pattern != '' and
                re.search('(' + input_pattern + ')$', context['input'])):
            return 0
        skip_length = (context['event'] != 'Manual' and
                       not (min_pattern_length <=
                            len(context['complete_str']) <=
                            max_pattern_length))
        return skip_length

    def position_has_changed(self, pos):
        return (pos != self.__vim.current.window.cursor or
                self.__vim.funcs.mode() != 'i')

    def check_recache(self):
        if self.__vim.options['runtimepath'] != self.__runtimepath:
            # Recache
            self.load_sources()
            self.load_filters()
            self.__runtimepath = self.__vim.options['runtimepath']

    def on_event(self, context):
        self.check_recache()

        for source_name, source in self.itersource(context):
            if hasattr(source, 'on_event'):
                source.on_event(context)
