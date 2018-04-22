# ============================================================================
# FILE: base.py
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
        self.matchers = ['matcher_fuzzy']
        self.sorters = ['sorter_rank']
        self.converters = [
            'converter_remove_overlap',
            'converter_truncate_abbr',
            'converter_truncate_kind',
            'converter_truncate_menu']
        self.filetypes = []
        self.keyword_patterns = []
        self.debug_enabled = False
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
        self.max_menu_width = 40
        self.max_candidates = 500

    def get_complete_position(self, context):
        keyword_pattern = self.vim.call(
            'deoplete#util#get_keyword_pattern',
            context['filetype'], self.keyword_patterns)
        m = re.search('(?:' + keyword_pattern + ')$', context['input'])
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

    def get_filetype_var(self, filetype, var_name):
        # Todo: buffer custom vars support

        var = self.vars[var_name]
        ft = filetype if (filetype in var) else '_'
        return var.get(ft, '')
