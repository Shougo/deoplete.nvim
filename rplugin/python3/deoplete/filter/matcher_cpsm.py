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

        self._cpsm = None

    def filter(self, context):
        if (not context['candidates'] or not context['input']
                or self._cpsm is False):
            return context['candidates']

        if self._cpsm is None:
            errmsg = self._init_cpsm(context)
            if errmsg:
                error(self.vim, 'matcher_cpsm: %s' % errmsg)
                return []

        complete_str = context['complete_str']
        if context['ignorecase']:
            complete_str = complete_str.lower()

        cpsm_result = self._get_cpsm_result(
            context['candidates'], complete_str)
        return [x for x in context['candidates']
                if x['word'] in sorted(cpsm_result, key=cpsm_result.index)]

    def _init_cpsm(self, context):
        ext = '.pyd' if context['is_windows'] else '.so'
        fname = 'bin/cpsm_py' + ext
        found = globruntime(self.vim.options['runtimepath'], fname)
        errmsg = None
        if found:
            sys.path.insert(0, os.path.dirname(found[0]))
            try:
                import cpsm_py
            except ImportError as exc:
                import traceback
                errmsg = 'Could not import cpsm_py: %s\n%s' % (
                    exc, traceback.format_exc())
            else:
                self._cpsm = cpsm_py
            finally:
                sys.path.pop(0)
        else:
            errmsg = (
                '%s was not found in runtimepath. '
                'You must install/build cpsm with Python 3 support.' % (
                    fname))
        if errmsg:
            self._cpsm = False
        return errmsg

    def _get_cpsm_result(self, candidates, pattern):
        return self._cpsm.ctrlp_match((d['word'] for d in candidates),
                                      pattern, limit=1000, ispath=False)[0]
