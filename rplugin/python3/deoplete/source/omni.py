# ============================================================================
# FILE: omni.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from .base import Base
from deoplete.util import (
    get_buffer_config, error, error_vim, convert2list,
    set_pattern, convert2candidates)


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'omni'
        self.mark = '[O]'
        self.rank = 500
        self.is_bytepos = True
        self.min_pattern_length = 0

        self.__prev_linenr = -1
        self.__prev_pos = -1
        self.__prev_input = ''
        self.__prev_candidates = []

        self.__input_patterns = {}
        set_pattern(self.__input_patterns, 'css,less,scss,sass',
                    [r'\w+', r'\w+[):;]?\s+\w*', r'[@!]'])
        set_pattern(self.__input_patterns, 'ruby',
                    [r'[^. \t0-9]\.\w*', r'[a-zA-Z_]\w*::\w*'])
        set_pattern(self.__input_patterns, 'javascript',
                    [r'[^. \t0-9]\.\w*'])
        set_pattern(self.__input_patterns, 'lua',
                    [r'\w+[.:]', r'require\s*\(?["'']\w*'])

    def get_complete_position(self, context):
        if self.__use_previous_result(context):
            return self.__prev_pos

        current_ft = self.vim.eval('&filetype')
        for filetype in context['filetypes']:
            for omnifunc in convert2list(
                    get_buffer_config(context, filetype,
                                      'deoplete_omni_functions',
                                      'deoplete#omni#functions',
                                      {'_': ''})):
                if omnifunc == '' and (filetype == current_ft or
                                       filetype in ['css', 'javascript']):
                    omnifunc = context['omni__omnifunc']
                if omnifunc == '' or not self.vim.call(
                            'deoplete#util#exists_omnifunc', omnifunc):
                    continue
                self.__omnifunc = omnifunc
                for input_pattern in convert2list(
                    get_buffer_config(context, filetype,
                                      'deoplete_omni_input_patterns',
                                      'deoplete#omni#input_patterns',
                                      self.__input_patterns)):

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
                        error(self.vim,
                              'omni source does not support: ' +
                              self.__omnifunc)
                        error(self.vim,
                              'You must use g:deoplete#omni_patterns' +
                              ' instead.')
                        return -1
                    try:
                        complete_pos = self.vim.call(self.__omnifunc, 1, '')
                    except:
                        error_vim(self.vim,
                                  'Error occurred calling omnifunction: ' +
                                  self.__omnifunc)
                        return -1
                    return complete_pos
        return -1

    def gather_candidates(self, context):
        if self.__use_previous_result(context):
            return self.__prev_candidates

        try:
            candidates = self.vim.call(
                self.__omnifunc, 0, context['complete_str'])
            if candidates is dict:
                candidates = candidates['words']
            elif candidates is int:
                candidates = []
        except:
            error_vim(self.vim,
                      'Error occurred calling omnifunction: ' +
                      self.__omnifunc)
            candidates = []

        candidates = convert2candidates(candidates)

        for candidate in candidates:
            candidate['dup'] = 1

        self.__prev_linenr = context['position'][1]
        self.__prev_pos = context['complete_position']
        self.__prev_input = context['input']
        self.__prev_candidates = candidates

        return candidates

    def __use_previous_result(self, context):
        return (context['position'][1] == self.__prev_linenr and
                re.sub(r'\w+$', '', context['input']) == re.sub(
                    r'\w+$', '', self.__prev_input) and
                len(context['input']) > len(self.__prev_input) and
                context['input'].find(self.__prev_input) == 0)
