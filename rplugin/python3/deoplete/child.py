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
                           import_plugin, get_custom, get_syn_names,
                           convert2candidates, uniq_list_dict)


class Child(logger.LoggingMixin):

    def __init__(self, vim):
        self.name = 'child'

        self._vim = vim
        self._filters = {}
        self._sources = {}
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

            for child_in in self._unpacker:
                name = child_in['name']
                args = child_in['args']
                queue_id = child_in['queue_id']

                ret = self.main(name, args, queue_id)
                if ret:
                    self._write(stdout, ret)

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
                error_tb(self._vim, 'Duplicated filter: %s' % f.name)
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
        results = self._gather_results(context)

        merged_results = []
        for result in [x for x in results
                       if not self._is_skip(x['context'], x['source'])]:
            candidates = self._get_candidates(
                result, context['input'], context['next_input'])
            if candidates:
                rank = get_custom(context['custom'],
                                  result['source'].name, 'rank',
                                  result['source'].rank)
                merged_results.append({
                    'complete_position': result['complete_position'],
                    'candidates': candidates,
                    'rank': rank,
                })

        is_async = len([x for x in results if x['is_async']]) > 0

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
            except Exception as exc:
                self._handle_source_exception(source, exc)

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
        except Exception as exc:
            self._handle_source_exception(source, exc)

    def _handle_source_exception(self, source, exc):
        if isinstance(exc, SourceInitError):
            error(self._vim,
                  'Error when loading source {}: {}. '
                  'Ignoring.'.format(source.name, exc))
            self._ignore_sources.append(source.name)
            return

        self._source_errors[source.name] += 1
        if source.is_silent:
            return
        if self._source_errors[source.name] > 2:
            error(self._vim, 'Too many errors from "%s". '
                  'This source is disabled until Neovim '
                  'is restarted.' % source.name)
            self._ignore_sources.append(source.name)
        else:
            error_tb(self._vim, 'Error from %s: %r' % (source.name, exc))

    def _process_filter(self, f, context, max_candidates):
        try:
            self._profile_start(context, f.name)
            if (isinstance(context['candidates'], dict) and
                    'sorted_candidates' in context['candidates']):
                filtered = []
                context['is_sorted'] = True
                for candidates in context['candidates']['sorted_candidates']:
                    context['candidates'] = candidates
                    filtered += f.filter(context)
            else:
                filtered = f.filter(context)
            if max_candidates > 0:
                filtered = filtered[: max_candidates]
            context['candidates'] = filtered
            self._profile_end(f.name)
        except Exception:
            error_tb(self._vim, 'Errors from: %s' % f)

    def _get_candidates(self, result, context_input, next_input):
        source = result['source']

        # Gather async results
        if result['is_async']:
            self._gather_async_results(result, source)

        if not result['candidates']:
            return None

        # Source context
        ctx = copy.deepcopy(result['context'])

        ctx['input'] = context_input
        ctx['next_input'] = next_input
        ctx['complete_str'] = context_input[ctx['char_position']:]
        ctx['is_sorted'] = False

        # Set ignorecase
        case = ctx['smartcase'] or ctx['camelcase']
        if case and re.search(r'[A-Z]', ctx['complete_str']):
            ctx['ignorecase'] = False
        ignorecase = ctx['ignorecase']

        # Match
        matchers = [self._filters[x] for x
                    in source.matchers if x in self._filters]
        if source.matcher_key != '':
            # Convert word key to matcher_key
            for candidate in ctx['candidates']:
                candidate['__save_word'] = candidate['word']
                candidate['word'] = candidate[source.matcher_key]
        for f in matchers:
            self._process_filter(f, ctx, source.max_candidates)
        if source.matcher_key != '':
            # Restore word key
            for candidate in ctx['candidates']:
                candidate['word'] = candidate['__save_word']

        # Sort and Convert
        sorters = [self._filters[x] for x
                   in source.sorters if x in self._filters]
        converters = [self._filters[x] for x
                      in source.converters if x in self._filters]
        for f in sorters + converters:
            self._process_filter(f, ctx, source.max_candidates)

        ctx['ignorecase'] = ignorecase

        # On post filter
        if hasattr(source, 'on_post_filter'):
            ctx['candidates'] = source.on_post_filter(ctx)

        mark = source.mark + ' '
        dup = bool(source.filetypes)
        for candidate in ctx['candidates']:
            # Set default menu and icase
            candidate['icase'] = 1
            if (mark != ' ' and
                    candidate.get('menu', '').find(mark) != 0):
                candidate['menu'] = mark + candidate.get('menu', '')
            if dup:
                candidate['dup'] = 1
        # Note: cannot use set() for dict
        if dup:
            # Remove duplicates
            ctx['candidates'] = uniq_list_dict(ctx['candidates'])

        return ctx['candidates']

    def _itersource(self, context):
        filetypes = context['filetypes']
        ignore_sources = set(self._ignore_sources)
        for ft in filetypes:
            ignore_sources.update(
                self._vim.call('deoplete#custom#_get_filetype_option',
                               'ignore_sources', ft, []))

        for source_name, source in self._get_sources().items():
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
            self._profile_flag = self._vim.call(
                'deoplete#custom#_get_option', 'profile')
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
        for ft in context['filetypes']:
            input_pattern = source.get_input_pattern(ft)
            if (input_pattern != '' and
                    re.search('(' + input_pattern + ')$', context['input'])):
                return False
        if context['event'] == 'Manual':
            return False
        return not (source.min_pattern_length <=
                    len(context['complete_str']) <= source.max_pattern_length)

    def _set_source_attributes(self, context):
        """Set source attributes from the context.

        Each item in `attrs` is the attribute name.
        """
        attrs = (
            'converters',
            'disabled_syntaxes',
            'filetypes',
            'input_pattern',
            'is_debug_enabled',
            'is_silent',
            'keyword_patterns',
            'mark',
            'matchers',
            'max_abbr_width',
            'max_candidates',
            'max_kind_width',
            'max_menu_width',
            'max_pattern_length',
            'min_pattern_length',
            'sorters',
        )

        for name, source in self._get_sources().items():
            for attr in attrs:
                source_attr = getattr(source, attr, None)
                custom = get_custom(context['custom'],
                                    name, attr, source_attr)
                if custom and isinstance(source_attr, dict):
                    # Update values if it is dict
                    source_attr.update(custom)
                else:
                    setattr(source, attr, custom)

            # Default min_pattern_length
            if source.min_pattern_length < 0:
                source.min_pattern_length = self._vim.call(
                    'deoplete#custom#_get_option', 'min_pattern_length')

            if not source.is_volatile:
                source.is_volatile = bool(source.filetypes)

    def _on_event(self, context):
        event = context['event']
        for source_name, source in self._itersource(context):
            if source.events is None or event in source.events:
                try:
                    source.on_event(context)
                except Exception as exc:
                    error_tb(self._vim, 'Exception during {}.on_event '
                             'for event {!r}: {}'.format(
                                 source_name, event, exc))

    def _get_sources(self):
        # Note: for the size change of "self._sources" error
        return copy.copy(self._sources)
