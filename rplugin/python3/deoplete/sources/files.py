#=============================================================================
# FILE: files.py
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
from glob import glob
from .base import Base

def parse_isfname(isfname):
    values = []
    parts = isfname.split(",")
    for part in parts:
        if re.match('\d+-\d+', part):
            "-".join(map(lambda x: chr(int(x)), part.split("-")))
        else:
            values += part
    return "".join(values)

def debug(vim, msg):
    vim.command('echomsg string("' + str(msg) + '")')

class Source(Base):
    def __init__(self):
        Base.__init__(self)

        self.name = 'files'
        self.mark = '[F]'

    def get_complete_position(self, vim, context):
        isfname = parse_isfname(vim.eval('&isfname'))
        # we need the last path available in the input,
        # so instead of building a complicated regex,
        # we reverse the input and search backwards
        reversed_input = context['input'][::-1]
        m = re.match('[A-Za-z' + isfname + ']*\/\.?', reversed_input)
        if m:
            # correct position
            return len(reversed_input) - m.end()
        else:
            return -1

    def gather_candidates(self, vim, context):
        candidates = glob(context['complete_str'] + '*')
        return [{ 'word': x } for x in sorted(candidates)]

