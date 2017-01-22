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

    def completion_begin(self, context):
        try:
            complete_position, candidates = self.gather_candidates(context)
        except Exception:
            error_tb(self._vim, 'Error while gathering completions')
            candidates = []

        if not candidates or self.position_has_changed(
                context['changedtick']) or self._vim.funcs.mode() != 'i':
            if 'deoplete#_saved_completeopt' in context['vars']:
                self._vim.call('deoplete#mapping#_restore_completeopt')
            return

        self._vim.vars['deoplete#_context'] = {
            'complete_position': complete_position,
            'changedtick': context['changedtick'],
            'candidates': candidates,
            'event': context['event'],
        }

        if context['event'] != 'Manual' and (
                'deoplete#_saved_completeopt' not in context['vars']):
            self._vim.call('deoplete#mapping#_set_completeopt')

        self._vim.feedkeys(context['start_complete'])
        if self._vim.call(
                'has', 'patch-7.4.1758') and context['event'] != 'Manual':
            self._vim.feedkeys('', 'x!')

    def gather_candidates(self, context):
        self.check_recache(context)

        # self.debug(context)

        results = self.gather_results(context)
        return self.merge_results(results)

    def gather_results(self, context):
        results = []

        for source_name, source in self.itersource(context):
            try:
                if source.disabled_syntaxes and 'syntax_names' not in context:
                    context['syntax_names'] = get_syn_names(self._vim)
                ctx = copy.deepcopy(context)
                charpos = source.get_complete_position(ctx)
                if charpos >= 0 and source.is_bytepos:
                    charpos = bytepos2charpos(
                        ctx['encoding'], ctx['input'], charpos)
                ctx['complete_str'] = ctx['input'][charpos:]
                ctx['complete_position'] = charpos2bytepos(
                    ctx['encoding'], ctx['input'], charpos)
                ctx['max_abbr_width'] = min(source.max_abbr_width,
                                            ctx['max_abbr_width'])
                ctx['max_menu_width'] = min(source.max_menu_width,
                                            ctx['max_menu_width'])
                if ctx['max_abbr_width'] > 0:
                    ctx['max_abbr_width'] = max(20, ctx['max_abbr_width'])
                if ctx['max_menu_width'] > 0:
                    ctx['max_menu_width'] = max(10, ctx['max_menu_width'])

                if charpos < 0 or self.is_skip(ctx, source.disabled_syntaxes,
                                               source.min_pattern_length,
                                               source.max_pattern_length,
                                               source.input_pattern):
                    # Skip
                    continue

                # Gathering
                self.profile_start(ctx, source.name)
                ctx['candidates'] = source.gather_candidates(ctx)
                self.profile_end(source.name)

                if 'candidates' not in ctx or not ctx['candidates']:
                    continue

                ctx['candidates'] = convert2candidates(ctx['candidates'])

                # Filtering
                ignorecase = ctx['ignorecase']
                smartcase = ctx['smartcase']
                camelcase = ctx['camelcase']

                # Set ignorecase
                if (smartcase or camelcase) and re.search(
                        r'[A-Z]', ctx['complete_str']):
                    ctx['ignorecase'] = 0

                filters = source.matchers + source.sorters + source.converters
                for f in [self._filters[x] for x
                          in filters if x in self._filters]:
                    try:
                        self.profile_start(ctx, f.name)
                        ctx['candidates'] = f.filter(ctx)
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

                ctx['ignorecase'] = ignorecase

                # On post filter
                if hasattr(source, 'on_post_filter'):
                    ctx['candidates'] = source.on_post_filter(ctx)

                # Set default menu and icase
                mark = source.mark + ' '
                for candidate in ctx['candidates']:
                    candidate['icase'] = 1
                    if (source.mark != '' and
                            candidate.get('menu', '').find(mark) != 0):
                        candidate['menu'] = mark + candidate.get('menu', '')
                    if source.filetypes:
                        candidate['dup'] = 1

                results.append({
                    'name': source_name,
                    'source': source,
                    'context': ctx,
                })
            except Exception:
                self._source_errors[source_name] += 1
                if self._source_errors[source_name] > 2:
                    error(self._vim, 'Too many errors from "%s". '
                          'This source is disabled until Neovim '
                          'is restarted.' % source_name)
                    self._ignored_sources.add(source.path)
                    self._sources.pop(source_name)
                    continue
                error_tb(self._vim,
                         'Could not get completions from: %s' % source_name)
        return results

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
