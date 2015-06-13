#=============================================================================
# FILE: tag.py
# AUTHOR: Felipe Morales <hel.sheep at gmail.com>
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
from .base import Base

class Source(Base):
    def __init__(self):
        Base.__init__(self)

        self.mark = '[T]'

    def get_complete_position(self, vim, context):
        m = re.search(context.input, r'[a-zA-Z_][a-zA-Z0-9_]')
        if m:
            return m.start()
        else:
            return -1

    def gather_candidates(self, vim, context):
        candidates = []
        p = re.compile('^[a-zA-Z_]\w*(?=\t)')

        for tags_file in vim.eval('tagfiles()'):
            with open(tags_file, 'r') as tags_file:
                for l in tags_file.readlines():
                    candidates += p.findall(l)
        return [{ 'word': x } for x in list(set(candidates))]
