# ============================================================================
# FILE: omni.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from .base import Base
from deoplete.util import (
    convert2list, set_pattern, convert2candidates)


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'omni'
        self.mark = '[O]'
        self.rank = 500
        self.is_bytepos = True
        self.min_pattern_length = 0

        input_patterns = {}
        set_pattern(input_patterns, 'css,less,scss,sass',
                    [r'\w{2}', r'\w+[):;]?\s*\w*', r'[@!]'])
        set_pattern(input_patterns, 'lua',
                    [r'\w+[.:]\w*', r'require\s*\(?["'']\w*'])
        self.vars = {
            'input_patterns': input_patterns,
            'functions': {},
        }

    def get_complete_position(self, context):
        current_ft = self.vim.eval('&filetype')

        for filetype in list(set([context['filetype']] +
                                 context['filetype'].split('.'))):
            pos = self._get_complete_position(context, current_ft, filetype)
            if pos >= 0:
                return pos
        return -1

    def _get_complete_position(self, context, current_ft, filetype):
        for omnifunc in convert2list(
                self.get_filetype_var(filetype, 'functions')):
            if omnifunc == '' and (filetype == current_ft or
                                   filetype in ['css', 'javascript']):
                omnifunc = context['omni__omnifunc']
            if omnifunc == '':
                continue
            self._omnifunc = omnifunc
            for input_pattern in convert2list(
                    self.get_filetype_var(filetype, 'input_patterns')):

                m = re.search('(' + input_pattern + ')$', context['input'])
                # self.debug(filetype)
                # self.debug(input_pattern)
                if input_pattern == '' or (context['event'] !=
                                           'Manual' and m is None):
                    continue

                if filetype == current_ft and self._omnifunc in [
                        'ccomplete#Complete',
                        'htmlcomplete#CompleteTags',
                        'LanguageClient#complete',
                        'phpcomplete#CompletePHP']:
                    # In the blacklist
                    return -1
                try:
                    complete_pos = self.vim.call(self._omnifunc, 1, '')
                except Exception as e:
                    self.print_error('Error occurred calling omnifunction: ' +
                                     self._omnifunc)
                    return -1
                return complete_pos
        return -1

    def gather_candidates(self, context):
        try:
            candidates = self.vim.call(self._omnifunc, 0, '')
            if isinstance(candidates, dict):
                candidates = candidates['words']
            elif isinstance(candidates, int):
                candidates = []
        except Exception as e:
            self.print_error('Error occurred calling omnifunction: ' +
                             self._omnifunc)
            candidates = []

        candidates = convert2candidates(candidates)

        for candidate in candidates:
            candidate['dup'] = 1

        return candidates
