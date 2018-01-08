# ============================================================================
# FILE: dp_main.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import sys
from neovim import attach


def attach_vim(serveraddr):
    if len(serveraddr.split(':')) == 2:
        serveraddr, port = serveraddr.split(':')
        port = int(port)
        vim = attach('tcp', address=serveraddr, port=port)
    else:
        vim = attach('socket', path=serveraddr)

    # sync path
    for path in vim.call(
            'globpath', vim.options['runtimepath'],
            'rplugin/python3', 1).split('\n'):
        sys.path.append(path)
    # Remove current path
    del sys.path[0]

    return vim


def main(serveraddr):
    vim = attach_vim(serveraddr)
    from deoplete.util import error
    for queue_id in sys.stdin:
        if 'deoplete#_child_in' not in vim.vars:
            continue
        if queue_id.strip() in vim.vars['deoplete#_child_in']:
            error(vim, queue_id)
    return


if __name__ == '__main__':
    main(sys.argv[1])
