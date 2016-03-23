# ============================================================================
# FILE: base.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from abc import abstractmethod
import deoplete.util


class Base(object):

    def __init__(self, vim):
        self.vim = vim
        self.name = 'base'
        self.description = ''

    @abstractmethod
    def filter(self, context):
        pass

    def debug(self, expr):
        deoplete.util.debug(self.vim, expr)
