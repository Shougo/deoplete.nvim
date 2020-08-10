# ============================================================================
# FILE: converter_word_abbr.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from deoplete.base.filter import Base
from deoplete.util import Nvim, UserContext, Candidates


class Filter(Base):
    def __init__(self, vim: Nvim) -> None:
        super().__init__(vim)

        self.name = 'converter_word_abbr'
        self.description = 'word abbr converter'

    def filter(self, context: UserContext) -> Candidates:
        for candidate in context['candidates']:
            candidate['abbr'] = candidate['word']
        return context['candidates']  # type: ignore
