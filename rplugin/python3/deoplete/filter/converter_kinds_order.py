# ============================================================================
# FILE: converter_reorder_kind.py
# AUTHOR: @reaysawa
# License: MIT license
# ============================================================================

from deoplete.filter.base import Base


class Filter(Base):
    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'converter_kinds_order'
        self.description = 'Reorder candidates based on their kind'

    def filter(self, context):
        preferred_order = self.vim.call(
            'deoplete#custom#_get_option', 'kinds_order'
        ).get(context['filetype'])
        if not context['candidates'] or not preferred_order:
            return context['candidates']

        max_list = self.vim.call('deoplete#custom#_get_option', 'max_list')

        context_candidates = context['candidates'][:]
        new_candidates = []
        new_candidates_len = 0

        for kind in preferred_order:
            disabled = kind[0] == '!'
            if disabled:
                kind = kind[1:]

            size = len(context_candidates)
            i = 0
            while i < size:
                if context_candidates[i]['kind'] == kind:
                    candidate = context_candidates.pop(i)
                    # effectively, i skips one position due to removal in-place
                    # decrease it so the "+1" at the bottom put it at the next
                    # position
                    i -= 1
                    size -= 1
                    if not disabled:
                        # raise Exception(candidate)
                        new_candidates.append(candidate)
                        new_candidates_len += 1
                        # stop filtering if the maximum has been achieved
                        if new_candidates_len == max_list:
                            return new_candidates
                i += 1

        # add remaining which were not filtered
        new_candidates.extend(context_candidates)

        return new_candidates
