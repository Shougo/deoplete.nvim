# ============================================================================
# FILE: matcher_full_fuzzy.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from deoplete.filter import matcher_fuzzy


class Filter(matcher_fuzzy.Filter):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'matcher_full_fuzzy'
        self.description = 'full fuzzy matcher'

    def filter(self, context):
        return super().filter(context, ensure_same_prefix=False)
