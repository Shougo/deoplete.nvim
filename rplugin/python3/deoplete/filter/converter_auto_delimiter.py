# ============================================================================
# FILE: converter_auto_delimiter.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from deoplete.base.filter import Base


class Filter(Base):
    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'converter_auto_delimiter'
        self.description = 'auto delimiter converter'
        self.vars = {
            'delimiters': ['/'],
        }

    def filter(self, context):
        delimiters = self.get_var('delimiters')
        for candidate, delimiter in [
                [x, last_find(x['abbr'], delimiters)]
                for x in context['candidates']
                if 'abbr' in x and x['abbr'] and
                not last_find(x['word'], delimiters) and
                last_find(x['abbr'], delimiters)]:
            candidate['word'] += delimiter
        return context['candidates']


def last_find(s, needles):
    for needle in needles:
        if len(s) >= len(needle) and s[-len(needle):] == needle:
            return needle
