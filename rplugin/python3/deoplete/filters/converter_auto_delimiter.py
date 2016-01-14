# ============================================================================
# FILE: converter_auto_delimiter.py
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

from .base import Base


class Filter(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'converter_auto_delimiter'
        self.description = 'auto delimiter converter'

    def filter(self, context):
        delimiters = self.vim.vars['deoplete#delimiters']
        for candidate, delimiter in [
                [x, last_find(x['abbr'], delimiters)[0]]
                for x in context['candidates']
                if ('abbr' in x) and not last_find(x['word'], delimiters) and
                last_find(x['abbr'], delimiters)]:
            candidate['word'] += delimiter
        return context['candidates']


def last_find(s, needles):
    return [x for x in needles if s.rfind(x) == (len(s) - len(x))]
