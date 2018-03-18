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
        self._vim.async_call(self._plugin._on_connection, transport)

    def pipe_data_received(self, fd, data):
        self._vim.async_call(self._plugin._on_output, fd, data)

    def process_exited(self):
        pass
