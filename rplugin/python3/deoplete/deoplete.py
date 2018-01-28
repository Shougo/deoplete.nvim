# ============================================================================
# FILE: deoplete.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from deoplete import logger
from deoplete.parent import Parent
from deoplete.util import (error_tb, find_rplugins)
# from deoplete.util import error


class Deoplete(logger.LoggingMixin):

    def __init__(self, vim):
        self.name = 'core'

        self._vim = vim
        self._runtimepath = ''
        self._custom = []
        self._loaded_paths = set()

        self._parents = []
        self._parent_count = 0
        self._max_parents = max(
            [1, self._vim.vars['deoplete#max_processes']])
        for n in range(0, self._max_parents):
            self._parents.append(Parent(vim))

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
        for parent in self._parents:
            parent.enable_logging()

    def completion_begin(self, context):
        self.debug('completion_begin: %s', context['input'])

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

        # Check the previous completion
        prev_candidates = context['vars'][
            'deoplete#_prev_completion']['candidates']
        if context['event'] == 'Async' and candidates == prev_candidates:
            return

        # error(self._vim, candidates)
        self._vim.vars['deoplete#_context'] = {
            'complete_position': position,
            'candidates': candidates,
            'event': context['event'],
            'input': context['input'],
            'is_async': is_async,
        }
        self._vim.call('deoplete#handler#_completion_timer_start')

        self.debug('completion_end: %s', context['input'])

    def merge_results(self, context):
        is_async = False
        merged_results = []
        for parent in self._parents:
            result = parent.merge_results(context)
            is_async = is_async or result[0]
            merged_results += result[1]

        if not merged_results:
            return (is_async, -1, [])

        complete_position = min([x['complete_position']
                                 for x in merged_results])

        all_candidates = []
        for result in merged_results:
            candidates = result['candidates']
            prefix = result['input'][
                complete_position:result['complete_position']]

            mark = result['mark'] + ' '
            for candidate in candidates:
                # Add prefix
                candidate['word'] = prefix + candidate['word']

                # Set default menu and icase
                candidate['icase'] = 1
                if (mark != ' ' and
                        candidate.get('menu', '').find(mark) != 0):
                    candidate['menu'] = mark + candidate.get('menu', '')
                if result['filetypes']:
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

            self._parents[self._parent_count].add_source(context, path)

            self._parent_count += 1
            self._parent_count %= self._max_parents

        self.set_source_attributes(context)
        self.set_custom(context)

    def load_filters(self, context):
        # Load filters from runtimepath
        for path in find_rplugins(context, 'filter'):
            if path in self._loaded_paths:
                continue
            self._loaded_paths.add(path)

            for parent in self._parents:
                parent.add_filter(path)

    def set_source_attributes(self, context):
        for parent in self._parents:
            parent.set_source_attributes(context)

    def set_custom(self, context):
        self._custom = context['custom']
        for parent in self._parents:
            parent.set_custom(self._custom)

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

        for parent in self._parents:
            parent.on_event(context)
