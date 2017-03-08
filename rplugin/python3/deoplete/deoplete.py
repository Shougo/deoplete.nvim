# ============================================================================
# FILE: deoplete.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================
import re
import copy
import time
import os.path

from collections import defaultdict

import deoplete.util  # noqa
import deoplete.filter  # noqa
import deoplete.source  # noqa

from deoplete import logger
from deoplete.exceptions import SourceInitError
from deoplete.util import (bytepos2charpos, charpos2bytepos, error, error_tb,
                           find_rplugins, get_buffer_config, get_custom,
                           get_syn_names, import_plugin, convert2candidates)


class Deoplete(logger.LoggingMixin):

    def __init__(self, vim):
        self._vim = vim
        self._filters = {}
        self._sources = {}
        self._runtimepath = ''
        self._custom = []
        self._profile_flag = None
        self._profile_start = 0
        self._source_errors = defaultdict(int)
        self._filter_errors = defaultdict(int)
        self.name = 'core'
        self._ignored_sources = set()
        self._ignored_filters = set()
        self._prev_linenr = -1
        self._prev_input = ''
        self._results = []

    def completion_begin(self, context):
        self.check_recache(context)

        try:
            is_async, complete_position, candidates = self.merge_results(
                self.gather_results(context), context['input'])

        except Exception:
            error_tb(self._vim, 'Error while gathering completions')

            is_async = False
            complete_position = -1
            candidates = []

        if is_async and self.use_previous_result(context):
            self._vim.call('deoplete#handler#_async_timer_start')
        else:
            self._vim.call('deoplete#handler#_async_timer_stop')

        if not candidates or self.position_has_changed(
                context['changedtick']) or self._vim.funcs.mode() != 'i':
            if 'deoplete#_saved_completeopt' in context['vars']:
                self._vim.call('deoplete#mapping#_restore_completeopt')
            return

        self._vim.vars['deoplete#_context'] = {
            'complete_position': complete_position,
            'candidates': candidates,
            'event': context['event'],
        }

        if context['event'] != 'Manual' and (
                'deoplete#_saved_completeopt' not in context['vars']):
            self._vim.call('deoplete#mapping#_set_completeopt')

        self._vim.call('deoplete#mapping#_do_complete')

    def gather_results(self, context):
        if not self.use_previous_result(context):
            self._prev_linenr = context['position'][1]
            self._prev_input = context['input']
            self._results = {}

        results = self._results

        for source in [x[1] for x in self.itersource(context)
                       if x[1].name not in results]:
            try:
                if source.disabled_syntaxes and 'syntax_names' not in context:
                    context['syntax_names'] = get_syn_names(self._vim)
                ctx = copy.deepcopy(context)
                ctx['is_async'] = False

                charpos = source.get_complete_position(ctx)
                if charpos >= 0 and source.is_bytepos:
                    charpos = bytepos2charpos(
                        ctx['encoding'], ctx['input'], charpos)

                ctx['char_position'] = charpos
                ctx['complete_position'] = charpos2bytepos(
                    ctx['encoding'], ctx['input'], charpos)
                ctx['complete_str'] = ctx['input'][ctx['char_position']:]

                if charpos < 0 or self.is_skip(ctx, source.disabled_syntaxes,
                                               source.min_pattern_length,
                                               source.max_pattern_length,
                                               source.input_pattern):
                    # Skip
                    continue

                ctx['max_abbr_width'] = min(source.max_abbr_width,
                                            ctx['max_abbr_width'])
                ctx['max_menu_width'] = min(source.max_menu_width,
                                            ctx['max_menu_width'])
                if ctx['max_abbr_width'] > 0:
                    ctx['max_abbr_width'] = max(20, ctx['max_abbr_width'])
                if ctx['max_menu_width'] > 0:
                    ctx['max_menu_width'] = max(10, ctx['max_menu_width'])

                # Gathering
                self.profile_start(ctx, source.name)
                ctx['candidates'] = source.gather_candidates(ctx)
                self.profile_end(source.name)

                if not ctx['is_async'] and ('candidates' not in ctx or
                                            not ctx['candidates']):
                    continue

                ctx['candidates'] = convert2candidates(ctx['candidates'])

                results[source.name] = {
                    'name': source.name,
                    'source': source,
                    'context': ctx,
                    'is_async': ctx['is_async'],
                }
            except Exception:
                self._source_errors[source.name] += 1
                if self._source_errors[source.name] > 2:
                    error(self._vim, 'Too many errors from "%s". '
                          'This source is disabled until Neovim '
                          'is restarted.' % source.name)
                    self._ignored_sources.add(source.path)
                    self._sources.pop(source.name)
                    continue
                error_tb(self._vim,
                         'Could not get completions from: %s' % source.name)

        return results.values()

    def merge_results(self, results, context_input):
        if not results:
            return (False, -1, [])

        complete_position = min(
            [x['context']['complete_position'] for x in results])

        candidates = []
        for result in results:
            source = result['source']

            # Gather async results
            if result['is_async']:
                result['context']['candidates'] += convert2candidates(
                    source.gather_candidates(result['context']))
                result['is_async'] = result['context']['is_async']

            context = copy.deepcopy(result['context'])

            context['input'] = context_input
            context['complete_str'] = context['input'][
                context['char_position']:]

            # Filtering
            ignorecase = context['ignorecase']
            smartcase = context['smartcase']
            camelcase = context['camelcase']

            # Set ignorecase
            if (smartcase or camelcase) and re.search(
                    r'[A-Z]', context['complete_str']):
                context['ignorecase'] = 0

            for f in [self._filters[x] for x
                      in source.matchers + source.sorters + source.converters
                      if x in self._filters]:
                try:
                    self.profile_start(context, f.name)
                    context['candidates'] = f.filter(context)
                    self.profile_end(f.name)
                except Exception:
                    self._filter_errors[f.name] += 1
                    if self._source_errors[f.name] > 2:
                        error(self._vim, 'Too many errors from "%s". '
                              'This filter is disabled until Neovim '
                              'is restarted.' % f.name)
                        self._ignored_filters.add(f.path)
                        self._filters.pop(f.name)
                        continue
                    error_tb(self._vim, 'Could not filter using: %s' % f)

            context['ignorecase'] = ignorecase

            # On post filter
            if hasattr(source, 'on_post_filter'):
                context['candidates'] = source.on_post_filter(context)

            prefix = context['input'][
                complete_position:context['complete_position']]

            mark = source.mark + ' '
            for candidate in context['candidates']:
                # Add prefix
                candidate['word'] = prefix + candidate['word']

                # Set default menu and icase
                candidate['icase'] = 1
                if (source.mark != '' and
                        candidate.get('menu', '').find(mark) != 0):
                    candidate['menu'] = mark + candidate.get('menu', '')
                if source.filetypes:
                    candidate['dup'] = 1

            candidates += context['candidates']

        # self.debug(candidates)
        if context['vars']['deoplete#max_list'] > 0:
            candidates = candidates[: context['vars']['deoplete#max_list']]

        is_async = len([x for x in results if x['context']['is_async']]) > 0

        return (is_async, complete_position, candidates)

    def itersource(self, context):
        sources = sorted(self._sources.items(),
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
                                  {}))

        for source_name, source in sources:
            if source.filetypes is None or source_name in ignore_sources:
                continue
            if context['sources'] and source_name not in context['sources']:
                continue
            if source.filetypes and not any(x in filetypes
                                            for x in source.filetypes):
                continue
            if not source.is_initialized and hasattr(source, 'on_init'):
                self.debug('on_init Source: %s', source.name)
                try:
                    source.on_init(context)
                except Exception as exc:
                    if isinstance(exc, SourceInitError):
                        error(self._vim,
                              'Error when loading source {}: {}. '
                              'Ignoring.'.format(source_name, exc))
                    else:
                        error_tb(self._vim,
                                 'Error when loading source {}: {}. '
                                 'Ignoring.'.format(source_name, exc))
                    self._ignored_sources.add(source.path)
                    self._sources.pop(source_name)
                    continue
                else:
                    source.is_initialized = True

            yield source_name, source

    def profile_start(self, context, name):
        if self._profile_flag is 0 or not self.debug_enabled:
            return

        if not self._profile_flag:
            self._profile_flag = context['vars']['deoplete#enable_profile']
            if self._profile_flag:
                return self.profile_start(context, name)
        elif self._profile_flag:
            self.debug('Profile Start: {0}'.format(name))
            self._profile_start = time.clock()

    def profile_end(self, name):
        if self._profile_start:
            self.debug('Profile End  : {0:<25} time={1:2.10f}'.format(
                name, time.clock() - self._profile_start))

    def load_sources(self, context):
        # Load sources from runtimepath
        loaded_paths = [source.path for source in self._sources.values()]
        for path in find_rplugins(context, 'source'):
            if path in self._ignored_sources:
                continue
            if path in loaded_paths:
                continue
            name = os.path.splitext(os.path.basename(path))[0]

            source = None
            try:
                Source = import_plugin(path, 'source', 'Source')
                if not Source:
                    continue

                source = Source(self._vim)
                source.name = getattr(source, 'name', name)
                source.path = path
                source.min_pattern_length = getattr(
                    source, 'min_pattern_length',
                    context['vars']['deoplete#auto_complete_start_length'])
                source.max_abbr_width = getattr(
                    source, 'max_abbr_width',
                    context['vars']['deoplete#max_abbr_width'])
                source.max_menu_width = getattr(
                    source, 'max_menu_width',
                    context['vars']['deoplete#max_menu_width'])
            except Exception:
                error_tb(self._vim, 'Could not load source: %s' % name)
            finally:
                if source:
                    self._sources[source.name] = source
                    self.debug('Loaded Source: %s (%s)', source.name, path)

        self.set_source_attributes(context)
        self._custom = context['custom']

    def load_filters(self, context):
        # Load filters from runtimepath
        loaded_paths = [filter.path for filter in self._filters.values()]
        for path in find_rplugins(context, 'filter'):
            if path in self._ignored_filters:
                continue
            if path in loaded_paths:
                continue
            name = os.path.splitext(os.path.basename(path))[0]

            f = None
            try:
                Filter = import_plugin(path, 'filter', 'Filter')
                if not Filter:
                    continue

                f = Filter(self._vim)
                f.name = getattr(f, 'name', name)
                f.path = path
                self._filters[f.name] = f
            except Exception:
                # Exception occurred when loading a filter.  Log stack trace.
                error_tb(self._vim, 'Could not load filter: %s' % name)
            finally:
                if f:
                    self._filters[f.name] = f
                    self.debug('Loaded Filter: %s (%s)', f.name, path)

    def set_source_attributes(self, context):
        """Set source attributes from the context.

        Each item in `attrs` is the attribute name.  If the default value is in
        context['vars'] under a different name, use a tuple.
        """
        attrs = (
            'filetypes',
            'disabled_syntaxes',
            'input_pattern',
            ('min_pattern_length', 'deoplete#auto_complete_start_length'),
            'max_pattern_length',
            ('max_abbr_width', 'deoplete#max_abbr_width'),
            ('max_menu_width', 'deoplete#max_menu_width'),
            'matchers',
            'sorters',
            'converters',
            'mark',
            'debug_enabled',
        )

        for name, source in self._sources.items():
            for attr in attrs:
                if isinstance(attr, tuple):
                    default_val = context['vars'][attr[1]]
                    attr = attr[0]
                else:
                    default_val = None
                source_attr = getattr(source, attr, default_val)
                setattr(source, attr, get_custom(context['custom'], name,
                                                 attr, source_attr))

    def use_previous_result(self, context):
        return self._results and (
            context['position'][1] == self._prev_linenr and
            re.sub(r'\w*$', '', context['input']) == re.sub(
                r'\w*$', '', self._prev_input) and
            len(context['input']) >= len(self._prev_input) and
            context['input'].find(self._prev_input) == 0)

    def is_skip(self, context, disabled_syntaxes,
                min_pattern_length, max_pattern_length, input_pattern):
        if 'syntax_names' in context and disabled_syntaxes:
            p = re.compile('(' + '|'.join(disabled_syntaxes) + ')$')
            if next(filter(p.search, context['syntax_names']), None):
                return True
        if (input_pattern != '' and
                re.search('(' + input_pattern + ')$', context['input'])):
            return False
        return (context['event'] != 'Manual' and
                not (min_pattern_length <=
                     len(context['complete_str']) <= max_pattern_length))

    def position_has_changed(self, tick):
        return tick != self._vim.eval('b:changedtick')

    def check_recache(self, context):
        if context['runtimepath'] != self._runtimepath:
            self.load_sources(context)
            self.load_filters(context)
            self._runtimepath = context['runtimepath']

            if context['rpc'] != 'deoplete_on_event':
                self.on_event(context)
        elif context['custom'] != self._custom:
            self.set_source_attributes(context)
            self._custom = context['custom']

    def on_event(self, context):
        self.debug('on_event: %s', context['event'])
        self.check_recache(context)

        for source_name, source in self.itersource(context):
            if hasattr(source, 'on_event'):
                self.debug('on_event: Source: %s', source_name)
                try:
                    source.on_event(context)
                except Exception as exc:
                    error_tb(self._vim, 'Exception during {}.on_event '
                             'for event {!r}: {}'.format(
                                 source_name, context['event'], exc))
