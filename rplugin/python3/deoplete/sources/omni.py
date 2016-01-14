# ============================================================================
# FILE: omni.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license  {{{
#     Permission is hereby granted, free of charge, to any person obtaining
#     a copy of this software and associated documentation files (the
#     "Software"), to deal in the Software without restriction, including
#     without limitation the rights to use, copy, modify, merge, publish,
#     distribute, sublicense, and/or sell copies of the Software, and to
#     permit persons to whom the Software is furnished to do so, subject to
#     the following conditions:
#
#     The above copyright notice and this permission notice shall be included
#     in all copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#     OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#     MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#     IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#     CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#     TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#     SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# }}}
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

        omnifunc = get_buffer_config(self.vim, context,
                                     'b:deoplete_omni_functions',
                                     'g:deoplete#omni#functions',
                                     'g:deoplete#omni#_functions')
        if omnifunc == '':
            omnifunc = self.vim.eval('&l:omnifunc')
        if omnifunc == '' or omnifunc == 'ccomplete#Complete':
            return -1
        for input_pattern in convert2list(
            get_buffer_config(self.vim, context,
                              'b:deoplete_omni_input_patterns',
                              'g:deoplete#omni#input_patterns',
                              'g:deoplete#omni#_input_patterns')):

            m = re.search('(' + input_pattern + ')$', context['input'])
            if input_pattern == '' or (context['event'] !=
                                       'Manual' and m is None):
                continue

            try:
                complete_pos = self.vim.call(omnifunc, 1, '')
            except:
                error(self.vim,
                      'Error occurred calling omnifunction: ' + omnifunc)
                return -1
            return complete_pos
        return -1

    def gather_candidates(self, context):
        if self.__use_previous_result(context):
            return self.__prev_candidates

        omnifunc = get_buffer_config(self.vim, context,
                                     'b:deoplete_omni_functions',
                                     'g:deoplete#omni#functions',
                                     'g:deoplete#omni#_functions')
        if omnifunc == '':
            omnifunc = self.vim.eval('&l:omnifunc')
        try:
            self.debug(omnifunc)
            candidates = self.vim.call(
                omnifunc, 0, context['complete_str'])
        except:
            error(self.vim,
                  'Error occurred calling omnifunction: ' + omnifunc)
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
                context['input'].find(self.__prev_input) == 0)
