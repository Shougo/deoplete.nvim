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
        self.__custom = []
        self.__profile_flag = None
        self.__profile_start = 0
        self.__encoding = self.__vim.options['encoding']
        self.name = 'core'

    def completion_begin(self, context):
        if context['event'] != 'Manual' and context['delay'] > 0:
            time.sleep(context['delay'] / 1000.0)
            if self.position_has_changed(context['changedtick']):
                return

        try:
            complete_position, candidates = self.gather_candidates(context)
        except Exception:
            for line in traceback.format_exc().splitlines():
                error(self.__vim, line)
            error(self.__vim,
                  'An error has occurred. Please execute :messages command.')
            candidates = []

        if not candidates or self.position_has_changed(
                context['changedtick']):
            return

        self.__vim.vars['deoplete#_context'] = {
            'complete_position': complete_position,
            'changedtick': context['changedtick'],
            'candidates': candidates,
            'event': context['event'],
        }

        self.__vim.feedkeys(context['start_complete'])

    def gather_candidates(self, context):
        self.check_recache(context)

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
                    self.__encoding, cont['input'], charpos)
            cont['complete_str'] = cont['input'][charpos:]
            cont['complete_position'] = charpos2bytepos(
                self.__encoding, cont['input'], charpos)
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
            self.profile_start(context, source.name)
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
                    self.profile_start(context, filter.name)
                    context['candidates'] = filter.filter(context)
                    self.profile_end(filter.name)
            finally:
                context['ignorecase'] = ignorecase
            # self.debug(context['candidates'])

            # On post filter
            if hasattr(source, 'on_post_filter'):
                context['candidates'] = source.on_post_filter(context)

            candidates = context['candidates']
            # Set default menu and icase
            mark = source.mark + ' '
            for candidate in candidates:
                candidate['icase'] = 1
                if source.mark != '' and candidate.get(
                        'menu', '').find(mark) != 0:
                    candidate['menu'] = mark + candidate.get('menu', '')

            # self.debug(context['candidates'])
        return results

    def itersource(self, context):
        sources = sorted(self.__sources.items(),
                         key=lambda x: get_custom(
                             context['custom'],
                             x[1].name, 'rank', x[1].rank),
                         reverse=True)
        filetypes = context['filetypes']
        ignore_sources = set()
        for ft in filetypes:
            ignore_sources.update(
                get_buffer_config(context, ft,
                                  'deoplete_ignore_sources',
                                  'deoplete#ignore_sources',
                                  'deoplete#_ignore_sources'))

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
        if context['vars']['deoplete#max_list'] > 0:
            candidates = candidates[: context['vars']['deoplete#max_list']]

        return (complete_position, candidates)

    def profile_start(self, context, name):
        if self.__profile_flag is 0 or not self.debug_enabled:
            return

        if self.__profile_flag is None:
            self.__profile_flag = context['vars']['deoplete#enable_profile']
            if self.__profile_flag:
                return self.profile_start(context, name)
        elif self.__profile_flag:
            self.debug('Profile Start: {0}'.format(name))
            self.__profile_start = time.clock()

    def profile_end(self, name):
        if self.__profile_start:
            self.debug('Profile End  : {0:<25} time={1:2.10f}'.format(
                name, time.clock() - self.__profile_start))

    def load_sources(self, context):
        # Load sources from runtimepath
        for path in globruntime(context['runtimepath'],
                                'rplugin/python3/deoplete/sources/base.py'
                                ) + globruntime(
                                    context['runtimepath'],
                                    'rplugin/python3/deoplete/sources/*.py'):
            name = os.path.basename(path)[: -3]
            module = importlib.machinery.SourceFileLoader(
                'deoplete.sources.' + name, path).load_module()
            self.debug(path)
            if not hasattr(module, 'Source') or name in self.__sources:
                continue

            source = module.Source(self.__vim)
            source.name = name
            source.min_pattern_length = getattr(
                source, 'min_pattern_length',
                context['vars']['deoplete#auto_complete_start_length'])
            source.max_abbr_width = getattr(
                source, 'max_abbr_width',
                context['vars']['deoplete#max_abbr_width'])
            source.max_menu_width = getattr(
                source, 'max_menu_width',
                context['vars']['deoplete#max_menu_width'])

            self.__sources[name] = source
            self.debug('Loaded Source: %s (%s)', name, module.__file__)

        self.set_source_attributes(context)
        self.__custom = context['custom']
        # self.debug(self.__sources)

    def load_filters(self, context):
        # Load filters from runtimepath
        for path in globruntime(context['runtimepath'],
                                'rplugin/python3/deoplete/filters/base.py'
                                ) + globruntime(
                                    context['runtimepath'],
                                    'rplugin/python3/deoplete/filters/*.py'):
            name = os.path.basename(path)[: -3]
            module = importlib.machinery.SourceFileLoader(
                'deoplete.filters.' + name, path).load_module()
            if hasattr(module, 'Filter') and name not in self.__filters:
                filter = module.Filter(self.__vim)
                self.__filters[filter.name] = filter
                self.debug('Loaded Filter: %s (%s)', name, module.__file__)
        # self.debug(self.__filters)

    def set_source_attributes(self, context):
        for source in self.__sources.values():
            source.filetypes = get_custom(
                context['custom'], source.name,
                'filetypes', source.filetypes)
            source.disabled_syntaxes = get_custom(
                context['custom'], source.name,
                'disabled_syntaxes', source.disabled_syntaxes)
            source.input_pattern = get_custom(
                context['custom'], source.name,
                'input_pattern', source.input_pattern)
            source.min_pattern_length = get_custom(
                context['custom'], source.name,
                'min_pattern_length',
                getattr(source, 'min_pattern_length',
                        context['vars'][
                            'deoplete#auto_complete_start_length']))
            source.max_pattern_length = get_custom(
                context['custom'], source.name,
                'max_pattern_length', source.max_pattern_length)
            source.max_abbr_width = get_custom(
                context['custom'], source.name,
                'max_abbr_width',
                getattr(source, 'max_abbr_width',
                        context['vars']['deoplete#max_abbr_width']))
            source.max_menu_width = get_custom(
                context['custom'], source.name,
                'max_menu_width',
                getattr(source, 'max_menu_width',
                        context['vars']['deoplete#max_menu_width']))
            source.matchers = get_custom(
                context['custom'], source.name,
                'matchers', source.matchers)
            source.sorters = get_custom(
                context['custom'], source.name,
                'sorters', source.sorters)
            source.converters = get_custom(
                context['custom'], source.name,
                'converters', source.converters)
            source.mark = get_custom(
                context['custom'], source.name,
                'mark', source.mark)
            source.debug_enabled = get_custom(
                context['custom'], source.name,
                'debug_enabled', source.debug_enabled)

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

    def position_has_changed(self, tick):
        return tick != self.__vim.eval('b:changedtick')

    def check_recache(self, context):
        if context['runtimepath'] != self.__runtimepath:
            self.load_sources(context)
            self.load_filters(context)
            self.__runtimepath = context['runtimepath']
        elif context['custom'] != self.__custom:
            self.set_source_attributes(context)
            self.__custom = context['custom']

    def on_event(self, context):
        self.check_recache(context)

        for source_name, source in self.itersource(context):
            if hasattr(source, 'on_event'):
                source.on_event(context)
