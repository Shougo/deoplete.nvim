# ============================================================================
# FILE: converter_auto_delimiter.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
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
