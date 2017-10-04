# ============================================================================
# FILE: omni.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from .base import Base
from deoplete.util import (
    get_buffer_config, convert2list, set_pattern, convert2candidates)


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'omni'
        self.mark = '[O]'
        self.rank = 500
        self.is_bytepos = True
        self.min_pattern_length = 0

        self._input_patterns = {}
        set_pattern(self._input_patterns, 'css,less,scss,sass',
                    [r'\w+', r'\w+[):;]?\s+\w*', r'[@!]'])
        set_pattern(self._input_patterns, 'lua',
                    [r'\w+[.:]\w*', r'require\s*\(?["'']\w*'])

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
                get_buffer_config(context, filetype,
                                  'deoplete_omni_functions',
                                  'deoplete#omni#functions',
                                  {'_': ''})):
            if omnifunc == '' and (filetype == current_ft or
                                   filetype in ['css', 'javascript']):
                omnifunc = context['omni__omnifunc']
            if omnifunc == '':
                continue
            self.__omnifunc = omnifunc
            for input_pattern in convert2list(
                    get_buffer_config(context, filetype,
                                      'deoplete_omni_input_patterns',
                                      'deoplete#omni#input_patterns',
                                      self._input_patterns)):

                m = re.search('(' + input_pattern + ')$', context['input'])
                # self.debug(filetype)
                # self.debug(input_pattern)
                if input_pattern == '' or (context['event'] !=
                                           'Manual' and m is None):
                    continue

                if filetype == current_ft and self.__omnifunc in [
                        'ccomplete#Complete',
                        'htmlcomplete#CompleteTags',
                        'phpcomplete#CompletePHP']:
                    # In the blacklist
                    self.print_error('omni source does not support: ' +
                                     self.__omnifunc)
                    self.print_error('You must use g:deoplete#omni_patterns' +
                                     ' instead.')
                    return -1
                try:
                    complete_pos = self.vim.call(self.__omnifunc, 1, '')
                except:
                    self.print_error('Error occurred calling omnifunction: ' +
                                     self.__omnifunc)
                    return -1
                return complete_pos
        return -1

    def gather_candidates(self, context):
        try:
            candidates = self.vim.call(self.__omnifunc, 0, '')
            if candidates is dict:
                candidates = candidates['words']
            elif candidates is int:
                candidates = []
        except:
            self.print_error('Error occurred calling omnifunction: ' +
                             self.__omnifunc)
            candidates = []

        candidates = convert2candidates(candidates)

        for candidate in candidates:
            candidate['dup'] = 1

        return candidates
