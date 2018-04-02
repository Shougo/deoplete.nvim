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
    description = ''
    mark = ''
    max_pattern_length = 80
    input_pattern = ''
    matchers = ['matcher_fuzzy']
    sorters = ['sorter_rank']
    converters = [
        'converter_remove_overlap',
        'converter_truncate_abbr',
        'converter_truncate_kind',
        'converter_truncate_menu',
    ]
    filetypes = []
    debug_enabled = False
    is_bytepos = False
    is_initialized = False
    is_volatile = False
    is_silent = False
    rank = 100
    disabled_syntaxes = []
    events = None

    def __init__(self, vim):
        self.vim = vim

    def get_complete_position(self, context):
        m = re.search('(?:' + context['keyword_patterns'] + ')$',
                      context['input'])
        return m.start() if m else -1

    def print(self, expr):
        if not self.is_silent:
            debug(self.vim, expr)

    def print_error(self, expr):
        if not self.is_silent:
            error_vim(self.vim, expr)

    @abstractmethod
    def gather_candidate(self, context):
        pass

    def on_event(self, context):
        pass
