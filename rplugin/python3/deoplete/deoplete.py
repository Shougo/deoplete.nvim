# ============================================================================
# FILE: deoplete.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import time
import os.path

import deoplete.util  # noqa
import deoplete.filter  # noqa
import deoplete.source  # noqa

from deoplete import logger
from deoplete.child import Child
from deoplete.util import (error_tb, find_rplugins, import_plugin)


class Deoplete(logger.LoggingMixin):

    def __init__(self, vim):
        self.name = 'core'

        self._vim = vim
        self._runtimepath = ''
        self._custom = []
        self._profile_flag = None
        self._profile_start = 0
        self._loaded_paths = set()

        self._children = []
        self._child_count = 0
        self._max_children = 5
        for n in range(0, self._max_children):
            self._children.append(Child(vim))

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
        for child in self._children:
            child.enable_logging()

    def completion_begin(self, context):
        self.check_recache(context)

        try:
            is_async, position, candidates = self.merge_results(context)
        except Exception:
            error_tb(self._vim, 'Error while gathering completions')

            is_async = False
            position = -1
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
            'complete_position': position,
            'candidates': candidates,
            'event': context['event'],
            'input': context['input'],
        }
        self._vim.call('deoplete#handler#_completion_timer_start')

    def merge_results(self, context):
        is_async = False
        merged_results = []
        for child in self._children:
            result = child.merge_results(context)
            is_async = is_async or result[0]
            merged_results += result[1]

        if not merged_results:
            return (is_async, -1, [])

        complete_position = min([x[1]['context']['complete_position']
                                 for x in merged_results])

        all_candidates = []
        for [candidates, result] in merged_results:
            ctx = result['context']
            source = result['source']
            prefix = ctx['input'][complete_position:ctx['complete_position']]

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
        max_list = context['vars']['deoplete#max_list']
        if max_list > 0:
            all_candidates = all_candidates[: max_list]

        return (is_async, complete_position, all_candidates)

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
                    self._children[self._child_count].add_source(source)
                    self._child_count += 1
                    self._child_count %= self._max_children
                    self.debug('Loaded Source: %s (%s)', source.name, path)

        self.set_source_attributes(context)
        self.set_custom(context)

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
            except Exception:
                # Exception occurred when loading a filter.  Log stack trace.
                error_tb(self._vim, 'Could not load filter: %s' % name)
            finally:
                if f:
                    for child in self._children:
                        child.add_filter(f)
                    self.debug('Loaded Filter: %s (%s)', f.name, path)

    def set_source_attributes(self, context):
        for child in self._children:
            child.set_source_attributes(context)

    def set_custom(self, context):
        self._custom = context['custom']
        for child in self._children:
            child.set_custom(self._custom)

    def check_recache(self, context):
        if context['runtimepath'] != self._runtimepath:
            self._runtimepath = context['runtimepath']
            self.load_sources(context)
            self.load_filters(context)

            if context['rpc'] != 'deoplete_on_event':
                self.on_event(context)
        elif context['custom'] != self._custom:
            self.set_source_attributes(context)
            self.set_custom(context)

    def on_event(self, context):
        self.debug('on_event: %s', context['event'])
        self.check_recache(context)

        for child in self._children:
            child.on_event(context)
