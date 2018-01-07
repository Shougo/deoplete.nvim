# ============================================================================
# FILE: child.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
import copy
import time

from collections import defaultdict
from threading import Thread
from queue import Queue
from neovim import attach

from deoplete import logger
from deoplete.exceptions import SourceInitError
from deoplete.util import (bytepos2charpos, charpos2bytepos, error, error_tb,
                           get_buffer_config, get_custom,
                           get_syn_names, convert2candidates)


class Child(logger.LoggingMixin):

    def __init__(self):
        self.name = 'child'

        self._vim = None
        self._filters = {}
        self._sources = {}
        self._custom = []
        self._profile_flag = None
        self._profile_start_time = 0
        self._source_errors = defaultdict(int)
        self._filter_errors = defaultdict(int)
        self._prev_results = {}

        self._thread = None
        self._queue_in = Queue()
        self._queue_out = Queue()

    def enable_logging(self):
        self.is_debug_enabled = True

    def add_source(self, s, serveraddr):
        self._start_thread(serveraddr)
        self._queue_put('add_source', [s])

    def add_filter(self, f):
        self._queue_put('add_filter', [f])

    def set_source_attributes(self, context):
        self._queue_put('set_source_attributes', [context])

    def set_custom(self, custom):
        self._queue_put('set_custom', [custom])

    def merge_results(self, context):
        self._queue_put('merge_results', [context])
        if self._queue_out.empty():
            return (False, [])
        return self._queue_out.get()

    def on_event(self, context):
        self._queue_put('on_event', [context])
        if context['event'] == 'VimLeavePre':
            self._stop_thread()

    def _start_thread(self, serveraddr):
        if not self._thread:
            self._thread = Thread(target=self._main_loop,
                                  args=(serveraddr,), daemon=True)
            self._thread.start()

    def _stop_thread(self):
        if self._thread:
            self._thread.join(1.0)
            self._thread = None

    def _queue_put(self, name, args):
        self._queue_in.put([name, args])

    def _attach_vim(self, serveraddr):
        if len(serveraddr.split(':')) == 2:
            serveraddr, port = serveraddr.split(':')
            port = int(port)
            self._vim = attach('tcp', address=serveraddr, port=port)
        else:
            self._vim = attach('socket', address=serveraddr)

    def _main_loop(self, serveraddr):
        self._vim.vars['hoge'] = 1
        self._attach_vim(serveraddr)

        while 1:
            self.debug('main_loop: begin')
            [message, args] = self._queue_in.get()
            self.debug('main_loop: %s', message)
            if message == 'add_source':
                self._add_source(args[0])
            elif message == 'add_filter':
                self._add_filter(args[0])
            elif message == 'set_source_attributes':
                self._set_source_attributes(args[0])
            elif message == 'set_custom':
                self._set_custom(args[0])
            elif message == 'on_event':
                self._on_event(args[0])
            elif message == 'merge_results':
                self._merge_results(args[0])

    def _add_source(self, s):
        self._sources[s.name] = s

    def _add_filter(self, f):
        self._filters[f.name] = f

    def _merge_results(self, context):
        results = self._gather_results(context)

        merged_results = []
        for result in [x for x in results
                       if not self._is_skip(x['context'], x['source'])]:
            source_result = self._source_result(result, context['input'])
            if source_result:
                merged_results.append(source_result)

        is_async = len([x for x in results if x['context']['is_async']]) > 0

        self._queue_out.put((is_async, merged_results))

    def _gather_results(self, context):
        results = []

        for source in [x[1] for x in self._itersource(context)]:
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

                if charpos < 0 or self._is_skip(ctx, source):
                    if source.name in self._prev_results:
                        self._prev_results.pop(source.name)
                    # Skip
                    continue

                if (source.name in self._prev_results and
                        self._use_previous_result(
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
                self._profile_start(ctx, source.name)
                ctx['candidates'] = source.gather_candidates(ctx)
                self._profile_end(source.name)

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

    def _gather_async_results(self, result, source):
        try:
            context = result['context']
            context['is_refresh'] = False
            async_candidates = source.gather_candidates(context)
            result['is_async'] = context['is_async']
            if async_candidates is None:
                return
            context['candidates'] += convert2candidates(async_candidates)
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

    def _process_filter(self, f, context):
        try:
            self._profile_start(context, f.name)
            if (isinstance(context['candidates'], dict) and
                    'sorted_candidates' in context['candidates']):
                context_candidates = []
                context['is_sorted'] = True
                for candidates in context['candidates']['sorted_candidates']:
                    context['candidates'] = candidates
                    context_candidates += f.filter(context)
                context['candidates'] = context_candidates
            else:
                context['candidates'] = f.filter(context)
            self._profile_end(f.name)
        except Exception:
            self._filter_errors[f.name] += 1
            if self._source_errors[f.name] > 2:
                error(self._vim, 'Too many errors from "%s". '
                      'This filter is disabled until Neovim '
                      'is restarted.' % f.name)
                self._filters.pop(f.name)
                return
            error_tb(self._vim, 'Errors from: %s' % f)

    def _source_result(self, result, context_input):
        source = result['source']

        # Gather async results
        if result['is_async']:
            self._gather_async_results(result, source)

        if not result['context']['candidates']:
            return []

        # Source context
        ctx = copy.deepcopy(result['context'])

        ctx['input'] = context_input
        ctx['complete_str'] = context_input[ctx['char_position']:]
        ctx['is_sorted'] = False

        # Set ignorecase
        case = ctx['smartcase'] or ctx['camelcase']
        if case and re.search(r'[A-Z]', ctx['complete_str']):
            ctx['ignorecase'] = 0
        ignorecase = ctx['ignorecase']

        # Filtering
        for f in [self._filters[x] for x
                  in source.matchers + source.sorters + source.converters
                  if x in self._filters]:
            self._process_filter(f, ctx)

        ctx['ignorecase'] = ignorecase

        # On post filter
        if hasattr(source, 'on_post_filter'):
            ctx['candidates'] = source.on_post_filter(ctx)

        if ctx['candidates']:
            return [ctx['candidates'], result]
        return []

    def _itersource(self, context):
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

    def _profile_start(self, context, name):
        if self._profile_flag is 0 or not self.is_debug_enabled:
            return

        if not self._profile_flag:
            self._profile_flag = context['vars']['deoplete#enable_profile']
            if self._profile_flag:
                return self._profile_start(context, name)
        elif self._profile_flag:
            self.debug('Profile Start: {0}'.format(name))
            self._profile_start_time = time.clock()

    def _profile_end(self, name):
        if self._profile_start_time:
            self.debug('Profile End  : {0:<25} time={1:2.10f}'.format(
                name, time.clock() - self._profile_start_time))

    def _use_previous_result(self, context, result, is_volatile):
        if context['position'][1] != result['prev_linenr']:
            return False
        if is_volatile:
            return context['input'] == result['prev_input']
        else:
            return (re.sub(r'\w*$', '', context['input']) ==
                    re.sub(r'\w*$', '', result['prev_input']) and
                    context['input'].find(result['prev_input']) == 0)

    def _is_skip(self, context, source):
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

    def _set_source_attributes(self, context):
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

    def _set_custom(self, custom):
        self._custom = custom

    def _on_event(self, context):
        for source_name, source in self._itersource(context):
            if hasattr(source, 'on_event'):
                self.debug('on_event: Source: %s', source_name)
                try:
                    source.on_event(context)
                except Exception as exc:
                    error_tb(self._vim, 'Exception during {}.on_event '
                             'for event {!r}: {}'.format(
                                 source_name, context['event'], exc))
