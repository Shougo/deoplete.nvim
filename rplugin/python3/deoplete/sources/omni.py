# ============================================================================
# FILE: omni.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from .base import Base
from deoplete.util import \
    get_buffer_config, error, convert2list


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'omni'
        self.mark = '[O]'
        self.rank = 500
        self.is_bytepos = True
        self.min_pattern_length = 0

        self.__prev_linenr = -1
        self.__prev_pos = -1
        self.__prev_input = ''
        self.__prev_candidates = []

    def get_complete_position(self, context):
        if self.__use_previous_result(context):
            return self.__prev_pos

        for filetype in context['filetypes']:
            omnifunc = get_buffer_config(self.vim, filetype,
                                         'b:deoplete_omni_functions',
                                         'g:deoplete#omni#functions',
                                         'g:deoplete#omni#_functions')
            if omnifunc == '':
                omnifunc = self.vim.current.buffer.options.get('omnifunc', '')
            if omnifunc == '' or [x for x in [
                    'ccomplete#Complete', 'htmlcomplete#CompleteTags']
                                  if x == omnifunc]:
                continue
            self.__omnifunc = omnifunc
            for input_pattern in convert2list(
                get_buffer_config(self.vim, filetype,
                                  'b:deoplete_omni_input_patterns',
                                  'g:deoplete#omni#input_patterns',
                                  'g:deoplete#omni#_input_patterns')):

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

        self.__prev_linenr = self.vim.funcs.line('.')
        self.__prev_pos = context['complete_position']
        self.__prev_input = context['input']
        self.__prev_candidates = candidates

        return candidates

    def __use_previous_result(self, context):
        return (self.vim.funcs.line('.') == self.__prev_linenr and
                re.sub(r'\w+$', '', context['input']) == re.sub(
                    r'\w+$', '', self.__prev_input) and
                len(context['input']) > len(self.__prev_input) and
                context['input'].find(self.__prev_input) == 0)
