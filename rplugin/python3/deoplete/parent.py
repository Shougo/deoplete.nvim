# ============================================================================
# FILE: parent.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import time

from deoplete import logger
from deoplete.process import Process
from deoplete.util import error


class Parent(logger.LoggingMixin):

    def __init__(self, vim):
        self.name = 'parent'

        self._vim = vim
        self._proc = None

        if 'deoplete#_child_in' not in self._vim.vars:
            self._vim.vars['deoplete#_child_in'] = {}
        if 'deoplete#_child_out' not in self._vim.vars:
            self._vim.vars['deoplete#_child_out'] = {}

    def enable_logging(self):
        self.is_debug_enabled = True

    def add_source(self, context, path):
        self._start_process(context, context['serveraddr'])
        self._put('add_source', [path])

    def add_filter(self, path):
        self._put('add_filter', [path])

    def set_source_attributes(self, context):
        self._put('set_source_attributes', [context])

    def set_custom(self, custom):
        self._put('set_custom', [custom])

    def merge_results(self, context):
        queue_id = self._put('merge_results', [context])
        if not queue_id:
            return (False, [])

        time.sleep(0.5)

        results = self._get(queue_id)
        return results if results else (False, [])

    def on_event(self, context):
        if context['event'] == 'VimLeavePre':
            self._stop_process()
        self._put('on_event', [context])

    def _start_process(self, context, serveraddr):
        if not self._proc:
            self._proc = Process(
                [context['python3'], context['dp_main'], serveraddr],
                context, context['cwd'])
            time.sleep(1)
            error(self._vim, self._proc.communicate(100))

    def _stop_process(self):
        if self._proc:
            self._proc.kill()
            self._proc = None

    def _put(self, name, args):
        if not self._proc:
            return None

        queue_id = str(time.time())

        child_in = self._vim.vars['deoplete#_child_in']
        child_in[queue_id] = {'name': name, 'args': args}
        self._vim.vars['deoplete#_child_in'] = child_in

        self._proc.write(queue_id + '\n')
        return queue_id

    def _get(self, queue_id):
        return self._vim.vars['deoplete#_child_out'].get(queue_id, None)
