# ============================================================================
# FILE: process.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import subprocess
import os


class Process(object):
    def __init__(self, commands, context, cwd):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.__proc = subprocess.Popen(commands,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL,
                                       startupinfo=startupinfo,
                                       cwd=cwd)
        self.__eof = False
        self.__context = context

    def eof(self):
        return self.__eof

    def kill(self):
        if not self.__proc:
            return
        self.__proc.kill()
        self.__proc.wait()
        self.__proc = None

    def write(self, text):
        self.__proc.stdin.write(text.encode(
            self.__context['encoding'], errors='replace'))
        self.__proc.stdin.flush()
