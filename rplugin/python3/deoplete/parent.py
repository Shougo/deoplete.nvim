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

    def enable_logging(self):
        self.is_debug_enabled = True

    def add_source(self, path, context):
        self._start_thread(context, context['serveraddr'])
        self._queue_put('add_source', [path])

    def add_filter(self, path):
        self._queue_put('add_filter', [path])

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

    def _start_thread(self, context, serveraddr):
        if not self._proc:
            self._proc = Process(
                [context['python3'], context['dp_main'], serveraddr],
                context, context['cwd'])
            time.sleep(1)
            error(self._vim, self._proc.communicate(100))

    def _stop_thread(self):
        if self._proc:
            self._proc.kill()
            self._proc = None

    def _queue_put(self, name, args):
        self._queue_in.put([name, args])
