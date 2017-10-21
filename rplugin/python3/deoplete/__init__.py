# ============================================================================
# FILE: __init__.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from importlib import find_loader
from deoplete import logger
from deoplete.deoplete import Deoplete


if not find_loader('yarp'):
    import neovim
    vim = neovim
else:
    import vim


class DeopleteHandlers(object):

    def __init__(self, vim):
        self._vim = vim

    def init_channel(self):
        self._deoplete = Deoplete(self._vim)
        self._vim.vars['deoplete#_initialized'] = True
        if hasattr(self._vim, 'channel_id'):
            self._vim.vars['deoplete#_channel_id'] = self._vim.channel_id

    def enable_logging(self, context):
        logging = self._vim.vars['deoplete#_logging']
        logger.setup(self._vim, logging['level'], logging['logfile'])
        self._deoplete.debug_enabled = True

    def auto_completion_begin(self, context):
        self._deoplete.completion_begin(context)

    def manual_completion_begin(self, context):
        self._deoplete.completion_begin(context)

    def on_event(self, context):
        self._deoplete.on_event(context)


deoplete_handler = DeopleteHandlers(vim)


def deoplete_init():
    deoplete_handler.init_channel()


def deoplete_enable_logging(context):
    deoplete_handler.enable_logging(context)


def deoplete_auto_completion_begin(context):
    deoplete_handler.auto_completion_begin(context)


def deoplete_manual_completion_begin(context):
    deoplete_handler.manual_completion_begin(context)


def deoplete_on_event(context):
    deoplete_handler.on_event(context)
