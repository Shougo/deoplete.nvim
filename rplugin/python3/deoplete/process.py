# ============================================================================
# FILE: process.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import subprocess
from threading import Thread
from queue import Queue
from time import time
import os


class Process(object):
    def __init__(self, commands, context, cwd):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.__proc = subprocess.Popen(commands,
                                       stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       startupinfo=startupinfo,
                                       cwd=cwd)
        self.__eof = False
        self.__context = context
        self.__queue_out = Queue()
        self.__thread = Thread(target=self.enqueue_output)
        self.__thread.start()

    def eof(self):
        return self.__eof

    def kill(self):
        if not self.__proc:
            return
        self.__proc.kill()
        self.__proc.wait()
        self.__proc = None
        self.__queue_out = None
        self.__thread.join(1.0)
        self.__thread = None

    def enqueue_output(self):
        for line in self.__proc.stdout:
            if not self.__queue_out:
                return
            self.__queue_out.put(
                line.decode(self.__context['encoding'],
                            errors='replace').strip('\r\n'))

    def communicate(self, timeout):
        if not self.__proc:
            return ([], [])

        start = time()
        outs = []

        while not self.__queue_out.empty() and time() < start + timeout:
            outs.append(self.__queue_out.get_nowait())

        if self.__thread.is_alive() or not self.__queue_out.empty():
            return (outs, [])

        _, errs = self.__proc.communicate(timeout=timeout)
        errs = errs.decode(self.__context['encoding'],
                           errors='replace').splitlines()
        self.__eof = True
        self.__proc = None
        self.__thread = None
        self.__queue = None

        return (outs, errs)
