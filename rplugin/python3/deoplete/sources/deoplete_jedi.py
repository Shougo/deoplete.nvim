from jedi import Script

from .base import Base
from deoplete import util


class Source(Base):
    def __init__(self, vim):
        # super(Base, self).__init__(vim)
        Base.__init__(self, vim)
        util.debug(vim, 'Init deoplete jedi')

        self.name = 'jedi'
        self.mark = '[J]'
        self.filetypes = ['python']

    def gather_candidates(self, context):
        util.debug(self.vim, 'Init deoplete jedi')

        util.debug(self.vim, context['input'])
        util.debug(self.vim, context['complete_pos'])
        util.debug(self.vim, context['complete_str'])
        util.debug(self.vim, context['filetype'])
        util.debug(self.vim, context['filetypes'])

        row, column = self.vim.current.window.cursor
        # If saved...
        buf = self.vim.current.buffer
        source = '\n'.join(buf[:])
        path = buf.name
        encoding = buf.options['fileencoding']

        script = Script(
            source=source,
            row=row,
            column=column,
            path=path,
            encoding=encoding,
        )

        return [
            {
                'word': completion.complete,
                'kind': completion.type.full_name,
            }
            for completion in script.completions()
        ]
