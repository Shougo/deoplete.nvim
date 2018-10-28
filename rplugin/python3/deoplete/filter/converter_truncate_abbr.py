# ============================================================================
# FILE: converter_truncate_abbr.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from deoplete.filter.base import Base
from deoplete.util import truncate_skipping


class Filter(Base):
    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'converter_truncate_abbr'
        self.description = 'truncate abbr converter'

    def filter(self, context):
        max_width = context['max_abbr_width']
        if max_width <= 0:
            return context['candidates']

        footer_width = max_width / 3
        for candidate in context['candidates']:
            candidate['abbr'] = truncate_skipping(
                candidate.get('abbr', candidate['word']),
                max_width, '..', footer_width)
        return context['candidates']
