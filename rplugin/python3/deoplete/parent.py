# ============================================================================
# FILE: parent.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import time

from deoplete import logger
from deoplete.process import Process
# from deoplete.util import error


class Parent(logger.LoggingMixin):

    def __init__(self, vim, context):
        self.name = 'parent'

        self._vim = vim
        self._proc = None
        self._queue_id = ''
        self._prev_pos = []
        self._start_process(context, context['serveraddr'])

    def enable_logging(self):
        self._put('enable_logging', [])
        self.is_debug_enabled = True

    def add_source(self, path):
        self._put('add_source', [path])

    def add_filter(self, path):
        self._put('add_filter', [path])

    def set_source_attributes(self, context):
        self._put('set_source_attributes', [context])

    def set_custom(self, custom):
        self._put('set_custom', [custom])

    def merge_results(self, context):
        if context['position'] == self._prev_pos and (
                self._queue_id or context['event'] == 'Async'):
            # Use previous id
            queue_id = self._queue_id
        else:
            queue_id = self._put('merge_results', [context])
            if not queue_id:
                return (False, [])

        get = self._get(queue_id)
        if not get:
            # Skip the next merge_results
            self._queue_id = queue_id
            self._prev_pos = context['position']
            return (True, [])
        self._queue_id = ''
        results = get[0]
        return (results['is_async'],
                results['merged_results']) if results else (False, [])

    def on_event(self, context):
        if context['event'] == 'VimLeavePre':
            self._stop_process()
            self._vim.vars['deoplete#_stopped_processes'] += 1
        self._put('on_event', [context])

    def _start_process(self, context, serveraddr):
        if self._proc:
            return

        python3 = self._vim.vars.get('python3_host_prog', 'python3')
        self._proc = Process(
            [python3, context['dp_main'], serveraddr],
            context, context['cwd'])

    def _stop_process(self):
        if self._proc:
            self._proc.kill()
            self._proc = None

    def _put(self, name, args):
        if not self._proc:
            return None

        queue_id = str(time.time())

        self._proc.write({'name': name, 'args': args, 'queue_id': queue_id})
        return queue_id

    def _get(self, queue_id):
        return [x for x in self._proc.communicate(15)
                if x['queue_id'] == queue_id]
