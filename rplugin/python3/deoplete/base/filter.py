# ============================================================================
# FILE: filter.py
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

    def get_var(self, var_name):
        custom_vars = self.vim.call(
            'deoplete#custom#_get_filter', self.name)
        if var_name in custom_vars:
            return custom_vars[var_name]
        if var_name in self.vars:
            return self.vars[var_name]
        return None

    @abstractmethod
    def filter(self, context):
        pass
