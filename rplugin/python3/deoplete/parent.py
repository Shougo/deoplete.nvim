# ============================================================================
# FILE: parent.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import time
import os
import msgpack
import subprocess
from functools import partial
from queue import Queue

from deoplete import logger
from deoplete.process import Process
from deoplete.util import error_tb, error

dp_main = os.path.join(os.path.dirname(__file__), 'dp_main.py')


class Parent(logger.LoggingMixin):

    def __init__(self, vim, context):
        self.name = 'parent'

        self._vim = vim
        self._hnd = None
        self._stdin = None
        self._child = None
        self._queue_id = ''
        self._prev_pos = []
        self._queue_in = Queue()
        self._queue_out = Queue()
        self._packer = msgpack.Packer(
            use_bin_type=True,
            encoding='utf-8',
            unicode_errors='surrogateescape')
        self._unpacker = msgpack.Unpacker(
            encoding='utf-8',
            unicode_errors='surrogateescape')
        self._start_process(context)

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
        if self._child:
            results = self._put('merge_results', [context])
        else:
            if context['position'] == self._prev_pos and self._queue_id:
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
        self._put('on_event', [context])

    def _start_process(self, context):
        num_processes = self._vim.call('deoplete#custom#_get_option',
                                       'num_processes')
        if num_processes != 1:
            # Parallel

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self._hnd = self._vim.loop.create_task(
                self._vim.loop.subprocess_exec(
                    partial(Process, self),
                    self._vim.vars.get('python3_host_prog', 'python3'),
                    dp_main,
                    self._vim.vars['deoplete#_serveraddr'],
                    stderr=None, cwd=context['cwd'], startupinfo=startupinfo))
        else:
            # Serial
            from deoplete.child import Child
            self._child = Child(self._vim)

    def _put(self, name, args):
        queue_id = str(time.time())

        if self._child:
            return self._child.main(name, args, queue_id)

        if not self._hnd:
            return None

        msg = self._packer.pack({
            'name': name, 'args': args, 'queue_id': queue_id
        })
        self._queue_in.put(msg)

        if self._stdin:
            try:
                while not self._queue_in.empty():
                    self._stdin.write(self._queue_in.get_nowait())
            except BrokenPipeError as e:
                error_tb(self._vim, 'Crash in child process')
                error(self._vim, 'stderr=' + str(self._proc.read_error()))
                self._hnd = None
        return queue_id

    def _get(self, queue_id):
        if not self._hnd:
            return []

        outs = []
        while not self._queue_out.empty():
            outs.append(self._queue_out.get_nowait())
        return [x for x in outs if x['queue_id'] == queue_id]
