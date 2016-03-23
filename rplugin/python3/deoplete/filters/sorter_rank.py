# ============================================================================
# FILE: sorter_rank.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from .base import Base


class Filter(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'sorter_rank'
        self.description = 'rank sorter'

    def filter(self, context):
        rank = self.vim.vars['deoplete#_rank']
        complete_str = context['complete_str'].lower()
        input_len = len(complete_str)
        return sorted(context['candidates'],
                      key=lambda x: -1 * rank[x['word']]
                      if x['word'] in rank
                      else abs(x['word'].lower().find(
                          complete_str, 0, input_len)))
