# ============================================================================
# FILE: process.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import asyncio


class Process(asyncio.SubprocessProtocol):

    def __init__(self, plugin):
        self._plugin = plugin
        self._vim = plugin._vim

    def connection_made(self, transport):
        self._plugin._stdin = transport.get_pipe_transport(0)

    def pipe_data_received(self, fd, data):
        unpacker = self._plugin._unpacker
        unpacker.feed(data)
        for child_out in unpacker:
            self._plugin._queue_out.put(child_out)

    def process_exited(self):
        pass
