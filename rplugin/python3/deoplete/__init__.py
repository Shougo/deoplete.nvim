# ============================================================================
# FILE: __init__.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================
import os
import re

from glob import glob

import neovim

from deoplete import logger
from deoplete.deoplete import Deoplete


@neovim.plugin
class DeopleteHandlers(object):

    def __init__(self, vim):
        self._vim = vim

    @neovim.function('_deoplete', sync=True)
    def init_python(self, args):
        self._deoplete = Deoplete(self._vim)
        self._vim.vars['deoplete#_channel_id'] = self._vim.channel_id

        # Check neovim-python version.
        try:
            import pkg_resources
            version = [pkg_resources.get_distribution('neovim').version]
        except Exception:
            version = []
            python_dir = os.path.dirname(os.path.dirname(neovim.__file__))
            base = python_dir + '/neovim-*/'
            for metadata in glob(base + 'PKG-INFO') + glob(base + '/METADATA'):
                with open(metadata, 'r', errors='replace') as f:
                    for line in f:
                        m = re.match('Version: (.+)', line)
                        if m:
                            version.append(m.group(1))
        self._vim.vars['deoplete#_neovim_python_version'] = version

    @neovim.rpc_export('deoplete_enable_logging')
    def enable_logging(self, level, logfile):
        logger.setup(self._vim, level, logfile)
        self._deoplete.debug_enabled = True

    @neovim.rpc_export('deoplete_auto_completion_begin')
    def completion_begin(self, context):
        context['rpc'] = 'deoplete_auto_completion_begin'
        self._deoplete.completion_begin(context)

    @neovim.rpc_export('deoplete_manual_completion_begin')
    def manual_completion_begin(self, context):
        context['rpc'] = 'deoplete_manual_completion_begin'
        self._deoplete.completion_begin(context)

    @neovim.rpc_export('deoplete_on_event')
    def on_event(self, context):
        context['rpc'] = 'deoplete_on_event'
        self._deoplete.on_event(context)
