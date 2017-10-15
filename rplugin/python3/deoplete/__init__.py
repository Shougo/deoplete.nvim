# ============================================================================
# FILE: __init__.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import vim

from deoplete import logger
from deoplete.deoplete import Deoplete


class DeopleteHandlers(object):

    def __init__(self, vim):
        self._vim = vim

    def init_channel(self):
        self._deoplete = Deoplete(self._vim)
        self._vim.vars['deoplete#_initialized'] = True

    def enable_logging(self, level, logfile):
        logger.setup(self._vim, level, logfile)
        self._deoplete.debug_enabled = True

    def auto_completion_begin(self, context):
        context['rpc'] = 'deoplete_auto_completion_begin'
        self._deoplete.completion_begin(context)

    def manual_completion_begin(self, context):
        context['rpc'] = 'deoplete_manual_completion_begin'
        self._deoplete.completion_begin(context)

    def on_event(self, context):
        context['rpc'] = 'deoplete_on_event'
        self._deoplete.on_event(context)


deoplete_handler = DeopleteHandlers(vim)


def deoplete_init():
    deoplete_handler.init_channel()


def deoplete_enable_logging(level, logfile):
    deoplete_handler.enable_logging(level, logfile)


def deoplete_auto_completion_begin(context):
    deoplete_handler.auto_completion_begin(context)


def deoplete_manual_completion_begin(context):
    deoplete_handler.manual_completion_begin(context)


def deoplete_on_event(context):
    deoplete_handler.on_event(context)
