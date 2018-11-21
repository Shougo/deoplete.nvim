# ============================================================================
# FILE: __init__.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from importlib.util import find_spec
from deoplete.deoplete import Deoplete


if find_spec('yarp'):
    import vim
elif find_spec('pynvim'):
    import pynvim
    vim = pynvim
else:
    import neovim
    vim = neovim

if hasattr(vim, 'plugin'):
    # Neovim only

    @vim.plugin
    class DeopleteHandlers(object):

        def __init__(self, vim):
            self._vim = vim

        @vim.function('_deoplete_init', sync=False)
        def init_channel(self, args):
            self._deoplete = Deoplete(self._vim)

        @vim.rpc_export('deoplete_enable_logging')
        def enable_logging(self, context):
            self._deoplete.enable_logging()

        @vim.rpc_export('deoplete_auto_completion_begin')
        def auto_completion_begin(self, context):
            self._deoplete.completion_begin(context)

        @vim.rpc_export('deoplete_manual_completion_begin')
        def manual_completion_begin(self, context):
            self._deoplete.completion_begin(context)

        @vim.rpc_export('deoplete_on_event')
        def on_event(self, context):
            self._deoplete.on_event(context)


if find_spec('yarp'):

    global_deoplete = Deoplete(vim)

    def deoplete_init():
        pass

    def deoplete_enable_logging(context):
        global_deoplete.enable_logging()

    def deoplete_auto_completion_begin(context):
        global_deoplete.completion_begin(context)

    def deoplete_manual_completion_begin(context):
        global_deoplete.completion_begin(context)

    def deoplete_on_event(context):
        global_deoplete.on_event(context)
