# ============================================================================
# FILE: delay.py
# AUTHOR: Tommy Allen <tommy at esdf.io>
# License: MIT license
# ============================================================================

from threading import Timer


class DelayTimer(object):
    """Reusable timer for delayed completions."""

    def __init__(self, vim):
        self.timer = None
        self.vim = vim

    def callback(self):
        self.vim.async_call(self.vim.call, 'deoplete#handler#_delay_trigger')

    def start(self, interval):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = Timer(interval, self.callback)
        self.timer.start()
