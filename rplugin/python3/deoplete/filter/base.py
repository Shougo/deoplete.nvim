# ============================================================================
# FILE: base.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from abc import abstractmethod
from deoplete.logger import LoggingMixin


class Base(LoggingMixin):
    name = 'base'
    description = ''

    def __init__(self, vim):
        self.vim = vim

    @abstractmethod
    def filter(self, context):
        pass
