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
    from deoplete.util import error_tb
    child = None
    try:
        from deoplete.child import Child
        child = Child(vim)
        while 1:
            child.main()
    except Exception:
        error_tb(vim, 'Error in child')
    return


if __name__ == '__main__':
    main(sys.argv[1])
