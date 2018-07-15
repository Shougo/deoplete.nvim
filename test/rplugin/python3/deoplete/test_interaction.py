import logging  # noqa: F401
import time

import _pytest
import pytest
from neovim.api.nvim import Nvim


def wait_until(f, timeout=1, interval=0.5):
    # Hide this frame in pytest errors.
    __tracebackhide__ = True

    tries = 0
    start = time.time()
    while not f():
        tries = tries + 1
        duration = time.time() - start
        if duration > timeout:
            pytest.fail('condition was not True after %.2fs (%d tries)' % (
                duration, tries))
        time.sleep(interval)
    return True


def test_bug(nvim: Nvim,
             request: _pytest.fixtures.FixtureRequest,
             neovim_logger: logging.Logger,
             ):
    force_normal = nvim.replace_termcodes(r'<C-\><C-n>')
    nvim.feedkeys(force_normal)

    # ctrl_p = nvim.replace_termcodes(r'<C-p>')

    nvim.current.buffer[:] = ['foo', 'foobar']
    nvim.command('norm gg')

    nvim.command('call deoplete#enable()')

    nvim.feedkeys('A', 'nt')
    wait_until(lambda: nvim.eval('pumvisible()'))

    # request.getfixturevalue('neovim_logger')

    # TODO: subscribe to popupmenu_show and use this to compare the actual
    # pum contents.
    # nvim.subscribe('popupmenu_show')

    # msgs = nvim._session._pending_messages
    # __import__('pdb').set_trace()
    # msg = msgs[-1]
    # assert msg == ('notification',
    #                b'redraw',
    #                [[b'popupmenu_show',
    #                  [[[b'foo', b'', b'[B] ', b''],
    #                    [b'foobar', b'', b'[B] ', b'']],
    #                   -1, 0, 0]]])

    nvim.feedkeys('n')
    wait_until(lambda: nvim.eval('!pumvisible()'))

    bs = nvim.replace_termcodes('<bs>')
    nvim.feedkeys(bs)
    nvim.feedkeys('A', 'nt')

    # XXX: this fails currently (#800)
    wait_until(lambda: nvim.eval('pumvisible()'))
