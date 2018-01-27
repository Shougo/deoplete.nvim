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
        self._loaded_paths = set()
        self._prev_results = {}

        # Enable logging before "Init" for more information, and e.g.
        # deoplete-jedi picks up the log filename from deoplete's handler in
        # its on_init.
        if self._vim.vars['deoplete#_logging']:
            self.enable_logging()

        # on_init() call
        context = self._vim.call('deoplete#init#_context', 'Init', [])
        context['rpc'] = 'deoplete_on_event'
        self.on_event(context)

        self._vim.vars['deoplete#_initialized'] = True
        if hasattr(self._vim, 'channel_id'):
            self._vim.vars['deoplete#_channel_id'] = self._vim.channel_id

    def enable_logging(self):
        logging = self._vim.vars['deoplete#_logging']
        logger.setup(self._vim, logging['level'], logging['logfile'])
        self.is_debug_enabled = True

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

        if is_async:
            self._vim.call('deoplete#handler#_async_timer_start')
        else:
            self._vim.call('deoplete#handler#_async_timer_stop')

        if not candidates and ('deoplete#_saved_completeopt'
                               in context['vars']):
            self._vim.call('deoplete#mapping#_restore_completeopt')

        # error(self._vim, context['input'])
        # error(self._vim, candidates)
        self._vim.vars['deoplete#_context'] = {
            'complete_position': complete_position,
            'candidates': candidates,
            'event': context['event'],
            'input': context['input'],
        }
        self._vim.call('deoplete#handler#_completion_timer_start')

    def gather_results(self, context):
        results = []

        for source in [x[1] for x in self.itersource(context)]:
            try:
                if source.disabled_syntaxes and 'syntax_names' not in context:
                    context['syntax_names'] = get_syn_names(self._vim)
                ctx = copy.deepcopy(context)

                charpos = source.get_complete_position(ctx)
                if charpos >= 0 and source.is_bytepos:
                    charpos = bytepos2charpos(
                        ctx['encoding'], ctx['input'], charpos)

                ctx['char_position'] = charpos
                ctx['complete_position'] = charpos2bytepos(
                    ctx['encoding'], ctx['input'], charpos)
                ctx['complete_str'] = ctx['input'][ctx['char_position']:]

                if charpos < 0 or self.is_skip(ctx, source):
                    if source.name in self._prev_results:
                        self._prev_results.pop(source.name)
                    # Skip
                    continue

                if (source.name in self._prev_results and
                        self.use_previous_result(
                            context, self._prev_results[source.name],
                            source.is_volatile)):
                    results.append(self._prev_results[source.name])
                    continue

                ctx['is_async'] = False
                ctx['is_refresh'] = True
                ctx['max_abbr_width'] = min(source.max_abbr_width,
                                            ctx['max_abbr_width'])
                ctx['max_kind_width'] = min(source.max_kind_width,
                                            ctx['max_kind_width'])
                ctx['max_menu_width'] = min(source.max_menu_width,
                                            ctx['max_menu_width'])
                if ctx['max_abbr_width'] > 0:
                    ctx['max_abbr_width'] = max(20, ctx['max_abbr_width'])
                if ctx['max_kind_width'] > 0:
                    ctx['max_kind_width'] = max(10, ctx['max_kind_width'])
                if ctx['max_menu_width'] > 0:
                    ctx['max_menu_width'] = max(10, ctx['max_menu_width'])

                # Gathering
                self.profile_start(ctx, source.name)
                ctx['candidates'] = source.gather_candidates(ctx)
                self.profile_end(source.name)

                if ctx['candidates'] is None:
                    continue

                ctx['candidates'] = convert2candidates(ctx['candidates'])

                result = {
                    'name': source.name,
                    'source': source,
                    'context': ctx,
                    'is_async': ctx['is_async'],
                    'prev_linenr': ctx['position'][1],
                    'prev_input': ctx['input'],
                }
                self._prev_results[source.name] = result
                results.append(result)
            except Exception:
                self._source_errors[source.name] += 1
                if source.is_silent:
                    continue
                if self._source_errors[source.name] > 2:
                    error(self._vim, 'Too many errors from "%s". '
                          'This source is disabled until Neovim '
                          'is restarted.' % source.name)
                    self._sources.pop(source.name)
                    continue
                error_tb(self._vim, 'Errors from: %s' % source.name)

        return results

    def gather_async_results(self, result, source):
        try:
            result['context']['is_refresh'] = False
            async_candidates = source.gather_candidates(result['context'])
            result['is_async'] = result['context']['is_async']
            if async_candidates is None:
                return
            result['context']['candidates'] += convert2candidates(
                async_candidates)
        except Exception:
            self._source_errors[source.name] += 1
            if source.is_silent:
                return
            if self._source_errors[source.name] > 2:
                error(self._vim, 'Too many errors from "%s". '
                      'This source is disabled until Neovim '
                      'is restarted.' % source.name)
                self._sources.pop(source.name)
            else:
                error_tb(self._vim, 'Errors from: %s' % source.name)

    def merge_results(self, results, context_input):
        merged_results = []
        all_candidates = []
        for result in [x for x in results
                       if not self.is_skip(x['context'], x['source'])]:
            source = result['source']

            # Gather async results
            if result['is_async']:
                self.gather_async_results(result, source)

            if not result['context']['candidates']:
                continue

            context = copy.deepcopy(result['context'])

            context['input'] = context_input
            context['complete_str'] = context['input'][
                context['char_position']:]
            context['is_sorted'] = False

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
                    if (isinstance(context['candidates'], dict) and
                            'sorted_candidates' in context['candidates']):
                        context_candidates = []
                        sorted_candidates = context['candidates'][
                            'sorted_candidates']
                        context['is_sorted'] = True
                        for candidates in sorted_candidates:
                            context['candidates'] = candidates
                            context_candidates += f.filter(context)
                        context['candidates'] = context_candidates
                    else:
                        context['candidates'] = f.filter(context)
                    self.profile_end(f.name)
                except Exception:
                    self._filter_errors[f.name] += 1
                    if self._source_errors[f.name] > 2:
                        error(self._vim, 'Too many errors from "%s". '
                              'This filter is disabled until Neovim '
                              'is restarted.' % f.name)
                        self._filters.pop(f.name)
                        continue
                    error_tb(self._vim, 'Errors from: %s' % f)

            context['ignorecase'] = ignorecase

            # On post filter
            if hasattr(source, 'on_post_filter'):
                context['candidates'] = source.on_post_filter(context)

            if context['candidates']:
                merged_results.append([context['candidates'], result])

        is_async = len([x for x in results if x['context']['is_async']]) > 0

        if not merged_results:
            return (is_async, -1, [])

        complete_position = min([x[1]['context']['complete_position']
                                 for x in merged_results])

        for [candidates, result] in merged_results:
            context = result['context']
            source = result['source']
            prefix = context['input'][
                complete_position:context['complete_position']]

            mark = source.mark + ' '
            for candidate in candidates:
                # Add prefix
                candidate['word'] = prefix + candidate['word']

                # Set default menu and icase
                candidate['icase'] = 1
                if (source.mark != '' and
                        candidate.get('menu', '').find(mark) != 0):
                    candidate['menu'] = mark + candidate.get('menu', '')
                if source.filetypes:
                    candidate['dup'] = 1

            all_candidates += candidates

        # self.debug(candidates)
        if context['vars']['deoplete#max_list'] > 0:
            all_candidates = all_candidates[
                : context['vars']['deoplete#max_list']]

        return (is_async, complete_position, all_candidates)

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
            if source.limit > 0 and context['bufsize'] > source.limit:
                continue
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
                    self._sources.pop(source_name)
                    continue
                else:
                    source.is_initialized = True
            yield source_name, source

    def profile_start(self, context, name):
        if self._profile_flag is 0 or not self.is_debug_enabled:
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
        for path in find_rplugins(context, 'source'):
            if path in self._loaded_paths:
                continue
            self._loaded_paths.add(path)

            name = os.path.splitext(os.path.basename(path))[0]

            source = None
            try:
                Source = import_plugin(path, 'source', 'Source')
                if not Source:
                    continue

                source = Source(self._vim)
                source.name = getattr(source, 'name', name)
                source.path = path
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
        for path in find_rplugins(context, 'filter'):
            if path in self._loaded_paths:
                continue
            self._loaded_paths.add(path)

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
            ('max_kind_width', 'deoplete#max_menu_width'),
            ('max_menu_width', 'deoplete#max_menu_width'),
            'matchers',
            'sorters',
            'converters',
            'mark',
            'is_debug_enabled',
            'is_silent',
        )

        for name, source in self._sources.items():
            for attr in attrs:
                if isinstance(attr, tuple):
                    default_val = context['vars'][attr[1]]
                    attr = attr[0]
                else:
                    default_val = None
                source_attr = getattr(source, attr, default_val)
                setattr(source, attr, get_custom(context['custom'],
                                                 name, attr, source_attr))

    def use_previous_result(self, context, result, is_volatile):
        if context['position'][1] != result['prev_linenr']:
            return False
        if is_volatile:
            return context['input'] == result['prev_input']
        else:
            return (re.sub(r'\w*$', '', context['input']) ==
                    re.sub(r'\w*$', '', result['prev_input']) and
                    context['input'].find(result['prev_input']) == 0)

    def is_skip(self, context, source):
        if 'syntax_names' in context and source.disabled_syntaxes:
            p = re.compile('(' + '|'.join(source.disabled_syntaxes) + ')$')
            if next(filter(p.search, context['syntax_names']), None):
                return True
        if (source.input_pattern != '' and
                re.search('(' + source.input_pattern + ')$',
                          context['input'])):
            return False
        if context['event'] == 'Manual':
            return False
        return not (source.min_pattern_length <=
                    len(context['complete_str']) <= source.max_pattern_length)

    def check_recache(self, context):
        if context['runtimepath'] != self._runtimepath:
            self._runtimepath = context['runtimepath']
            self.load_sources(context)
            self.load_filters(context)

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
