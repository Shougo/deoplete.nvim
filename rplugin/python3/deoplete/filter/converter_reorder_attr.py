# ============================================================================
# FILE: converter_reorder_attr.py
# AUTHOR: @reaysawa
# License: MIT license
# ============================================================================

from deoplete.filter.base import Base
import re


class Filter(Base):
    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'converter_reorder_attr'
        self.description = 'Reorder candidates based on their attributes'

    def filter(self, context):
        preferred_order_attrs = self.vim.call(
            'deoplete#custom#_get_option', 'attrs_order'
        ).get(context['filetype'])
        if not context['candidates'] or not preferred_order_attrs:
            return context['candidates']

        max_list = self.vim.call('deoplete#custom#_get_option', 'max_list')

        context_candidates = context['candidates'][:]
        new_candidates = []
        new_candidates_len = 0

        for attr in keys(preferred_order_attrs):
            for expr in preferred_order_attrs[attr]:
                disabled = expr[0] == '!'
                if disabled:
                    expr = expr[1:]

                expr = re.compile(expr)
                size = len(context_candidates)
                i = 0
                while i < size:
                    if expr.search(context_candidates[i][attr]):
                        candidate = context_candidates.pop(i)
                        # Popping will make 'i' effectively go forward 2 pos;
                        # because of that, decrease for now and wait for the
                        # +1 at the bottom to balance that out.
                        i -= 1
                        size -= 1
                        if not disabled:
                            new_candidates.append(candidate)
                            new_candidates_len += 1
                            # stop filtering if the maximum has been achieved
                            if new_candidates_len == max_list:
                                return new_candidates
                    i += 1

            # add remaining which were not filtered
            new_candidates.extend(context_candidates)
            # do the same again until all attrs have been sorted
            context_candidates = new_candidates

        return new_candidates
