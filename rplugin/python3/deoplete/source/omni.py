# ============================================================================
# FILE: omni.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from .base import Base
from deoplete.util import \
    get_buffer_config, error, convert2list, set_pattern


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
                    ['\w+', r'\w+[):;]?\s+\w*', r'[@!]'])
        set_pattern(self.__input_patterns, 'ruby',
                    [r'[^. \t0-9]\.\w*', r'[a-zA-Z_]\w*::\w*'])
        set_pattern(self.__input_patterns, 'lua',
                    [r'\w+[.:]', r'require\s*\(?["'']\w*'])

    def get_complete_position(self, context):
        if self.__use_previous_result(context):
            return self.__prev_pos

        for filetype in context['filetypes']:
            omnifunc = get_buffer_config(context, filetype,
                                         'deoplete_omni_functions',
                                         'deoplete#omni#functions',
                                         {'_': ''})
            if omnifunc == '':
                omnifunc = context['omni__omnifunc']
            if omnifunc == '' or [x for x in [
                    'ccomplete#Complete', 'htmlcomplete#CompleteTags']
                                  if x == omnifunc]:
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

                try:
                    complete_pos = self.vim.call(self.__omnifunc, 1, '')
                except:
                    error(self.vim,
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
            error(self.vim,
                  'Error occurred calling omnifunction: ' +
                  self.__omnifunc)
            candidates = []

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
