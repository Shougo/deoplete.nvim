# ============================================================================
# FILE: matcher_head.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from .base import Base


class Filter(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'matcher_head'
        self.description = 'head matcher'

    def filter(self, context):
        complete_str = context['complete_str']
        if context['ignorecase']:
            complete_str = complete_str.lower()
        if context['ignorecase']:
            return [x for x in context['candidates']
                    if x['word'].lower().startswith(complete_str)]
        else:
            return [x for x in context['candidates']
                    if x['word'].startswith(complete_str)]
