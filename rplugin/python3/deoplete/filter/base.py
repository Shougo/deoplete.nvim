# ============================================================================
# FILE: base.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from abc import abstractmethod
from deoplete.logger import LoggingMixin


class Base(LoggingMixin):

    def __init__(self, vim):
        self.vim = vim
        self.name = 'base'
        self.description = ''

    def on_event(self, context):
        pass

    @abstractmethod
    def filter(self, context):
        pass
