# ============================================================================
# FILE: source.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from abc import abstractmethod
from deoplete.logger import LoggingMixin
from deoplete.util import debug, error_vim


class Base(LoggingMixin):

    def __init__(self, vim):
        self.vim = vim
        self.description = ''
        self.mark = ''
        self.max_pattern_length = 80
        self.min_pattern_length = -1
        self.input_pattern = ''
        self.input_patterns = {}
        self.matchers = ['matcher_fuzzy']
        self.sorters = ['sorter_rank']
        self.converters = [
            'converter_remove_overlap',
            'converter_truncate_abbr',
            'converter_truncate_kind',
            'converter_truncate_info',
            'converter_truncate_menu']
        self.filetypes = []
        self.keyword_patterns = []
        self.is_debug_enabled = False
        self.is_bytepos = False
        self.is_initialized = False
        self.is_volatile = False
        self.is_silent = False
        self.rank = 100
        self.disabled_syntaxes = []
        self.events = None
        self.vars = {}
        self.max_abbr_width = 80
        self.max_kind_width = 40
        self.max_info_width = 200
        self.max_menu_width = 40
        self.max_candidates = 500
        self.matcher_key = ''
        self.dup = False

    def get_complete_position(self, context):
        m = re.search('(?:' + context['keyword_pattern'] + ')$|$',
                      context['input'])
        return m.start() if m else -1

    def print(self, expr):
        if not self.is_silent:
            debug(self.vim, expr)

    def print_error(self, expr):
        if not self.is_silent:
            error_vim(self.vim, expr)

    @abstractmethod
    def gather_candidates(self, context):
        pass

    def on_event(self, context):
        pass

    def get_var(self, var_name):
        custom_vars = self.vim.call(
            'deoplete#custom#_get_source_vars', self.name)
        if var_name in custom_vars:
            return custom_vars[var_name]
        if var_name in self.vars:
            return self.vars[var_name]
        return None

    def get_filetype_var(self, filetype, var_name):
        var = self.get_var(var_name)
        if var is None:
            return None
        ft = filetype if (filetype in var) else '_'
        return var.get(ft, '')

    def get_input_pattern(self, filetype):
        if not self.input_patterns:
            return self.input_pattern

        ft = filetype if (filetype in self.input_patterns) else '_'
        return self.input_patterns.get(ft, self.input_pattern)

    def get_buf_option(self, option):
        return self.vim.call('getbufvar', '%', '&' + option)
