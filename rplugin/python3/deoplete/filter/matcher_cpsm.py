# ============================================================================
# FILE: matcher_cpsm.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from .base import Base
import sys
import os
from deoplete.util import error, globruntime


class Filter(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'matcher_cpsm'
        self.description = 'cpsm matcher'

        self.__initialized = False
        self.__disabled = False

    def filter(self, context):
        if not context['candidates'] or not context[
                'input'] or self.__disabled:
            return context['candidates']

        if not self.__initialized:
            # cpsm installation check
            ext = '.pyd' if context['is_windows'] else '.so'
            if globruntime(context['runtimepath'], 'bin/cpsm_py' + ext):
                # Add path
                sys.path.append(os.path.dirname(
                    globruntime(context['runtimepath'],
                                'bin/cpsm_py' + ext)[0]))
                self.__initialized = True
            else:
                error(self.vim, 'matcher_cpsm: bin/cpsm_py' + ext +
                      ' is not found in your runtimepath.')
                error(self.vim, 'matcher_cpsm: You must install/build' +
                      ' Python3 support enabled cpsm.')
                self.__disabled = True
                return []

        cpsm_result = self._get_cpsm_result(
            context['candidates'], context['complete_str'])
        return [x for x in context['candidates']
                if x['word'] in sorted(cpsm_result, key=cpsm_result.index)]

    def _get_cpsm_result(self, candidates, pattern):
        import cpsm_py
        return cpsm_py.ctrlp_match((d['word'] for d in candidates),
                                   pattern, limit=1000, ispath=False)[0]
