# ============================================================================
# FILE: converter_truncate_menu.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from .base import Base
from deoplete.util import truncate_skipping


class Filter(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'converter_truncate_menu'
        self.description = 'truncate menu converter'

    def filter(self, context):
        if not context['candidates'] or 'menu' not in context[
                'candidates'][0]:
            return context['candidates']

        max_width = context['max_menu_width']
        footer_width = max_width / 3
        for candidate in context['candidates']:
            candidate['menu'] = truncate_skipping(
                candidate.get('menu', ''),
                max_width, '..', footer_width)
        return context['candidates']
