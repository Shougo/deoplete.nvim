# ============================================================================
# FILE: converter_reorder_kind.py
# AUTHOR: @reaysawa
# License: MIT license
# ============================================================================

from deoplete.filter.base import Base


class Filter(Base):
    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'converter_reorder_kind'
        self.description = 'Reorder candidates based on their kind'

    def filter(self, context):
        preferred_order = self.vim.call(
            'deoplete#custom#_get_option', 'kind_order_preference'
        ).get(context['filetype'])
        if not context['candidates'] or not preferred_order:
            return context['candidates']

        max_list = (self.vim.call('deoplete#custom#_get_option', 'max_list'))
        new_candidates = []
        new_candidates_len = 0

        for kind in preferred_order:
            disabled = kind[0] == '!'
            if disabled:
                kind = kind[1:]

            size = len(context['candidates'])
            i = 0
            while i < size:
                if context['candidates'][i]['kind'] == kind:
                    candidate = context['candidates'].pop(i)
                    size -= 1
                    if not disabled:
                        new_candidates.append(candidate)
                        new_candidates_len += 1
                        # stop filtering if the maximum has been achieved
                        if new_candidates_len == max_list:
                            return new_candidates
                i += 1

        # add remaining which were not filtered
        new_candidates.extend(context['candidates'])

        return new_candidates
