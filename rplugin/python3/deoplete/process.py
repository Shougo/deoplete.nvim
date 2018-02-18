# ============================================================================
# FILE: process.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import subprocess
import os
import msgpack
from threading import Thread
from queue import Queue
from time import time, sleep


class Process(object):
    def __init__(self, commands, context, cwd):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self._proc = subprocess.Popen(commands,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      startupinfo=startupinfo,
                                      cwd=cwd)
        self._context = context
        self._packer = msgpack.Packer(
            use_bin_type=True,
            encoding='utf-8',
            unicode_errors='surrogateescape')
        self._unpacker = msgpack.Unpacker(
            encoding='utf-8',
            unicode_errors='surrogateescape')
        self._queue_out = Queue()
        self._thread = Thread(target=self.enqueue_output)
        self._thread.start()

    def kill(self):
        if not self._proc:
            return
        self._proc.kill()
        self._proc.wait()
        self._proc = None
        self._queue_out = None
        self._thread.join(1.0)
        self._thread = None

    def enqueue_output(self):
        while self._proc and self._proc.stdout:
            b = self._proc.stdout.raw.read(102400)
            if b is None:
                continue
            if b == b'':
                # EOF
                break
            self._unpacker.feed(b)
            for child_out in self._unpacker:
                self._queue_out.put(child_out)

    def communicate(self, timeout):
        if not self._proc:
            return []

        end = time() + timeout
        while self._queue_out.empty() and time() < end:
            sleep(0.005)

        outs = []
        while not self._queue_out.empty():
            outs.append(self._queue_out.get_nowait())
        return outs

    def read_error(self):
        if not self._proc or not self._proc.stderr:
            return ''
        return self._proc.stderr.read()

    def write(self, expr):
        if not self._proc or not self._proc.stdin:
            return
        self._proc.stdin.write(self._packer.pack(expr))
        self._proc.stdin.flush()
