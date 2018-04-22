# ============================================================================
# FILE: deoplete.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from deoplete import logger
from deoplete.parent import Parent
from deoplete.util import (error_tb, find_rplugins, error)


class Deoplete(logger.LoggingMixin):

    def __init__(self, vim):
        self.name = 'core'

        self._vim = vim
        self._runtimepath = ''
        self._custom = []
        self._loaded_paths = set()
        self._prev_merged_results = {}
        self._prev_pos = []

        self._parents = []
        self._parent_count = 0
        self._max_parents = self._vim.call('deoplete#custom#_get_option',
                                           'num_processes')

        if self._max_parents != 1 and not hasattr(self._vim, 'loop'):
            error(self._vim, 'neovim-python 0.2.4+ is required.')
            return

        # Enable logging for more information, and e.g.
        # deoplete-jedi picks up the log filename from deoplete's handler in
        # its on_init.
        if self._vim.vars['deoplete#_logging']:
            self.enable_logging()

        # Initialization
        context = self._vim.call('deoplete#init#_context', 'Init', [])
        context['rpc'] = 'deoplete_on_event'
        self._check_recache(context)

        if hasattr(self._vim, 'channel_id'):
            self._vim.vars['deoplete#_channel_id'] = self._vim.channel_id
        self._vim.vars['deoplete#_initialized'] = True

    def enable_logging(self):
        logging = self._vim.vars['deoplete#_logging']
        logger.setup(self._vim, logging['level'], logging['logfile'])
        self.is_debug_enabled = True

    def completion_begin(self, context):
        self.debug('completion_begin: %s', context['input'])

        self._check_recache(context)

        try:
            is_async, position, candidates = self._merge_results(context)
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

        # Async update is skipped if same.
        prev_completion = context['vars']['deoplete#_prev_completion']
        prev_candidates = prev_completion['candidates']
        prev_pos = prev_completion['complete_position']
        if (context['event'] == 'Async' and
                prev_pos == self._vim.call('getpos', '.') and
                prev_candidates and candidates == prev_candidates):
            return

        # error(self._vim, candidates)
        self._vim.vars['deoplete#_context'] = {
            'complete_position': position,
            'candidates': candidates,
            'event': context['event'],
            'input': context['input'],
            'is_async': is_async,
        }
        self._vim.call('deoplete#handler#_do_complete')

        self.debug('completion_end: %s', context['input'])

    def on_event(self, context):
        self.debug('on_event: %s', context['event'])
        self._check_recache(context)

        for parent in self._parents:
            parent.on_event(context)

    def _merge_results(self, context):
        use_prev = (context['position'] == self._prev_pos
                    and context['event'] != 'Manual')
        if not use_prev:
            self._prev_merged_results = {}

        is_async = False
        merged_results = []
        for cnt, parent in enumerate(self._parents):
            if use_prev and cnt in self._prev_merged_results:
                # Use previous result
                merged_results += self._prev_merged_results[cnt]
            else:
                result = parent.merge_results(context)
                is_async = is_async or result[0]
                if not result[0]:
                    self._prev_merged_results[cnt] = result[1]
                merged_results += result[1]
        self._prev_pos = context['position']

        if not merged_results:
            return (is_async, -1, [])

        complete_position = min([x['complete_position']
                                 for x in merged_results])

        all_candidates = []
        for result in sorted(merged_results,
                             key=lambda x: x['rank'], reverse=True):
            candidates = result['candidates']
            prefix = context['input'][
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
                if result['dup']:
                    candidate['dup'] = 1

            all_candidates += candidates

        # self.debug(candidates)
        max_list = self._vim.call('deoplete#custom#_get_option', 'max_list')
        if max_list > 0:
            all_candidates = all_candidates[: max_list]

        return (is_async, complete_position, all_candidates)

    def _add_parent(self, context):
        parent = Parent(self._vim, context)
        if self._vim.vars['deoplete#_logging']:
            parent.enable_logging()
        self._parents.append(parent)

    def _init_parents(self, context):
        if self._parents or self._max_parents <= 0:
            return

        for n in range(0, self._max_parents):
            self._add_parent(context)

    def _load_sources(self, context):
        self._init_parents(context)

        # Load sources from runtimepath
        for path in find_rplugins(context, 'source'):
            if path in self._loaded_paths:
                continue
            self._loaded_paths.add(path)

            if self._max_parents <= 0:
                # Add parent automatically
                self._add_parent(context)

            self._parents[self._parent_count].add_source(path)
            self.debug('Process %d: %s', self._parent_count, path)

            self._parent_count += 1
            if self._max_parents > 0:
                self._parent_count %= self._max_parents

        self._set_source_attributes(context)
        self._set_custom(context)

    def _load_filters(self, context):
        # Load filters from runtimepath
        for path in find_rplugins(context, 'filter'):
            if path in self._loaded_paths:
                continue
            self._loaded_paths.add(path)

            for parent in self._parents:
                parent.add_filter(path)

    def _set_source_attributes(self, context):
        for parent in self._parents:
            parent.set_source_attributes(context)

    def _set_custom(self, context):
        self._custom = context['custom']
        for parent in self._parents:
            parent.set_custom(self._custom)

    def _check_recache(self, context):
        if context['runtimepath'] != self._runtimepath:
            self._runtimepath = context['runtimepath']
            self._load_sources(context)
            self._load_filters(context)

            if context['rpc'] != 'deoplete_on_event':
                self.on_event(context)
        elif context['custom'] != self._custom:
            self._set_source_attributes(context)
            self._set_custom(context)
