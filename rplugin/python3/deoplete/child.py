# ============================================================================
# FILE: child.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import copy
import os.path
import re
import sys
import time
import msgpack

from collections import defaultdict

import deoplete.source  # noqa
import deoplete.filter  # noqa

from deoplete import logger
from deoplete.exceptions import SourceInitError
from deoplete.util import (bytepos2charpos, charpos2bytepos, error, error_tb,
                           import_plugin,
                           get_buffer_config, get_custom,
                           get_syn_names, convert2candidates)


class Child(logger.LoggingMixin):

    def __init__(self, vim):
        self.name = 'child'

        self._vim = vim
        self._filters = {}
        self._sources = {}
        self._custom = []
        self._profile_flag = None
        self._profile_start_time = 0
        self._loaded_sources = {}
        self._loaded_filters = {}
        self._source_errors = defaultdict(int)
        self._prev_results = {}
        self._unpacker = msgpack.Unpacker(
            encoding='utf-8',
            unicode_errors='surrogateescape')
        self._packer = msgpack.Packer(
            use_bin_type=True,
            encoding='utf-8',
            unicode_errors='surrogateescape')
        self._ignore_sources = []

    def main_loop(self, stdout):
        while True:
            feed = sys.stdin.buffer.raw.read(102400)
            if feed is None:
                continue
            if feed == b'':
                # EOF
                return

            self._unpacker.feed(feed)
            self.debug('_read: %d bytes', len(feed))

            for child_in in self._unpacker:
                name = child_in['name']
                args = child_in['args']
                queue_id = child_in['queue_id']
                self.debug('main_loop: %s begin', name)

                ret = self.main(name, args, queue_id)
                if ret:
                    self._write(stdout, ret)

                self.debug('main_loop: end')

    def main(self, name, args, queue_id):
        ret = None
        if name == 'enable_logging':
            self._enable_logging()
        elif name == 'add_source':
            self._add_source(args[0])
        elif name == 'add_filter':
            self._add_filter(args[0])
        elif name == 'set_source_attributes':
            self._set_source_attributes(args[0])
        elif name == 'set_custom':
            self._set_custom(args[0])
        elif name == 'on_event':
            self._on_event(args[0])
        elif name == 'merge_results':
            ret = self._merge_results(args[0], queue_id)
        return ret

    def _write(self, stdout, expr):
        stdout.buffer.write(self._packer.pack(expr))
        stdout.flush()

    def _enable_logging(self):
        logging = self._vim.vars['deoplete#_logging']
        logger.setup(self._vim, logging['level'], logging['logfile'])
        self.is_debug_enabled = True

    def _add_source(self, path):
        source = None
        try:
            Source = import_plugin(path, 'source', 'Source')
            if not Source:
                return

            source = Source(self._vim)
            name = os.path.splitext(os.path.basename(path))[0]
            source.name = getattr(source, 'name', name)
            source.path = path
            if source.name in self._loaded_sources:
                # Duplicated name
                error_tb(self._vim, 'Duplicated source: %s' % source.name)
                error_tb(self._vim, 'path: "%s" "%s"' %
                         (path, self._loaded_sources[source.name]))
                source = None
        except Exception:
            error_tb(self._vim, 'Could not load source: %s' % path)
        finally:
            if source:
                self._loaded_sources[source.name] = path
                self._sources[source.name] = source
                self.debug('Loaded Source: %s (%s)', source.name, path)

    def _add_filter(self, path):
        f = None
        try:
            Filter = import_plugin(path, 'filter', 'Filter')
            if not Filter:
                return

            f = Filter(self._vim)
            name = os.path.splitext(os.path.basename(path))[0]
            f.name = getattr(f, 'name', name)
            f.path = path
            if f.name in self._loaded_filters:
                # Duplicated name
                error_tb(self._vim, 'duplicated filter: %s' % f.name)
                error_tb(self._vim, 'path: "%s" "%s"' %
                         (path, self._loaded_filters[f.name]))
                f = None
        except Exception:
            # Exception occurred when loading a filter.  Log stack trace.
            error_tb(self._vim, 'Could not load filter: %s' % path)
        finally:
            if f:
                self._loaded_filters[f.name] = path
                self._filters[f.name] = f
                self.debug('Loaded Filter: %s (%s)', f.name, path)

    def _merge_results(self, context, queue_id):
        self.debug('merged_results: begin')
        results = self._gather_results(context)

        merged_results = []
        for result in [x for x in results
                       if not self._is_skip(x['context'], x['source'])]:
            source_result = self._source_result(result, context['input'])
            if source_result:
                rank = get_custom(self._custom,
                                  result['source'].name, 'rank',
                                  result['source'].rank)
                merged_results.append({
                    'complete_position': source_result['complete_position'],
                    'mark': result['source'].mark,
                    'dup': bool(result['source'].filetypes),
                    'candidates': result['candidates'],
                    'source_name': result['source'].name,
                    'rank': rank,
                })

        is_async = len([x for x in results if x['context']['is_async']]) > 0

        self.debug('merged_results: end')
        return {
            'queue_id': queue_id,
            'is_async': is_async,
            'merged_results': merged_results,
        }

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
                    'input': ctx['input'],
                    'complete_position': ctx['complete_position'],
                    'candidates': ctx['candidates'],
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
                    self._ignore_sources.append(source.name)
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
                self._ignore_sources.append(source.name)
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
            error_tb(self._vim, 'Errors from: %s' % f)

    def _source_result(self, result, context_input):
        source = result['source']

        # Gather async results
        if result['is_async']:
            self._gather_async_results(result, source)

        if not result['candidates']:
            return None

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

        result['candidates'] = ctx['candidates']
        return result if result['candidates'] else None

    def _itersource(self, context):
        filetypes = context['filetypes']
        ignore_sources = set(self._ignore_sources)
        for ft in filetypes:
            ignore_sources.update(
                get_buffer_config(context, ft,
                                  'deoplete_ignore_sources',
                                  'deoplete#ignore_sources',
                                  {}))

        for source_name, source in self._sources.items():
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
                    self._ignore_sources.append(source_name)
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
