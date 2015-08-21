#=============================================================================
# FILE: member.py
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
#=============================================================================

import re
import operator
import functools
from deoplete.util import \
    set_default, set_pattern, \
    get_default_buffer_config, debug, charpos2bytepos
from .base import Base

class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'member'
        self.mark = '[M]'
        self.buffers = {}
        self.min_pattern_length = 0

        # Initialize member prefix patterns
        set_default(self.vim,
                    'g:deoplete#member#prefix_patterns', {})
        set_default(self.vim,
                    'g:deoplete#member#_prefix_patterns', {})
        set_pattern(self.vim,
                    'g:deoplete#member#_prefix_patterns',
                    'c,objc', r'\.|->')
        set_pattern(self.vim,
                    'g:deoplete#member#_prefix_patterns',
                    'cpp,objcpp', r'\.|->|::')
        set_pattern(self.vim,
                    'g:deoplete#member#_prefix_patterns',
                    'perl,php', r'->')
        set_pattern(self.vim,
                    'g:deoplete#member#_prefix_patterns',
                    'cs,java,javascript,d,vim,ruby,python,perl6,scala,vb',
                    r'\.')
        set_pattern(self.vim,
                    'g:deoplete#member#_prefix_patterns',
                    'cs,java,javascript,d,vim,ruby,python,perl6,scala,vb',
                    r'\.')
        set_pattern(self.vim,
                    'g:deoplete#member#_prefix_patterns',
                    'ruby', r'\.|::')
        set_pattern(self.vim,
                    'g:deoplete#member#_prefix_patterns',
                    'lua', r'\.|:')

        # Initialize member object pattern
        self.object_pattern = r'[a-zA-Z_]\w*(?:\(\)?)?'

    def get_complete_position(self, context):
        # Check member prefix pattern.
        prefix_pattern = get_default_buffer_config(
            self.vim, context,
            'b:deoplete_member_prefix_patterns',
            'g:deoplete#member#prefix_patterns',
            'g:deoplete#member#_prefix_patterns')
        if prefix_pattern == '':
            return -1
        m = re.search(self.object_pattern + prefix_pattern + r'\w*$',
                    context['input'])
        if m is None:
            return -1
        self.prefix = re.sub('\w*$', '', m.group(0))
        return re.search(r'\w*$', context['input']).start()

    def gather_candidates(self, context):
        p = re.compile(r'(?<=' + re.escape(self.prefix) + r')\w+(?:\(\)?)?')

        return [{ 'word': x } for x in
                functools.reduce(operator.add, [
                     p.findall(x) for x in self.vim.current.buffer
                     ])]

