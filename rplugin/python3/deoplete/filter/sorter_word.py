# ============================================================================
# FILE: sorter_word.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from deoplete.filter.base import Base


class Filter(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'sorter_word'
        self.description = 'word sorter'

    def filter(self, context):
        return sorted(context['candidates'],
                      key=lambda x: x['word'].swapcase())
