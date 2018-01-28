# ============================================================================
# FILE: process.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import subprocess
import os
import msgpack


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
        self._eof = False
        self._context = context
        self._unpacker = msgpack.Unpacker(encoding='utf-8')

    def eof(self):
        return self._eof

    def kill(self):
        if not self._proc:
            return
        self._proc.kill()
        self._proc.wait()
        self._proc = None

    def read(self):
        while 1:
            b = self._proc.stdout.read(1)
            self._unpacker.feed(b)
            for child_out in self._unpacker:
                return child_out

    def write(self, expr):
        self._proc.stdin.write(msgpack.packb(expr, use_bin_type=True))
        self._proc.stdin.flush()
