import logging  # noqa: F401
import time

import _pytest
import pytest
from neovim.api.nvim import Nvim


def wait_until(f, timeout=1, interval=0.1):
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


def popupmsgs(msgs):
    # ('notification',
    #  b'redraw',
    #  [[b'popupmenu_show',
    #    [[[b'foo', b'', b'[B] ', b''],
    #      [b'foobar', b'', b'[B] ', b'']],
    #     -1, 0, 0]]])
    return [
        msg
        for msg in msgs
        if (
            msg[0] == "notification"
            and msg[1] == b"redraw"
            and msg[2][0][0].startswith(b"popupmenu_")
        )
    ]


@pytest.fixture
def setup_buffer(nvim):
    force_normal = nvim.replace_termcodes(r'<C-\><C-n>')
    nvim.feedkeys(force_normal)

    nvim.current.buffer[:] = ['foo', 'foobar']
    nvim.command('norm gg0')


@pytest.mark.parametrize('sleep', ('sleep', 'nosleep'))
@pytest.mark.parametrize('method', ('ctrlp', 'bs', 'esc-C'))
def test_after_backspace(method, sleep, setup_buffer, nvim: Nvim,
                         request: _pytest.fixtures.FixtureRequest,
                         # neovim_logger: logging.Logger,
                         ):
    """Test various methods around issue #800."""
    bs = nvim.replace_termcodes('<bs>')
    ctrl_p = nvim.replace_termcodes(r'<C-p>')
    esc = nvim.replace_termcodes(r'<esc>')

    nvim.command('call deoplete#enable()')

    nvim.feedkeys('A')
    wait_until(lambda: nvim.eval('pumvisible()'))

    nvim.feedkeys('n')
    wait_until(lambda: nvim.eval('!pumvisible()'))

    # Related to autocmds?!
    # nvim.command('au CompleteDone * echom "CD"')

    # TODO: subscribe to popupmenu_show and use this to compare the actual
    # pum contents.
    msgs = nvim._session._pending_messages
    # popups = popupmsgs(msgs)
    msgs.clear()

    assert nvim.current.line == 'foon'

    if sleep == 'sleep':
        time.sleep(0.1)

    nvim.feedkeys(bs)
    assert nvim.current.line == 'foo'

    if method == 'ctrlp':
        # Ctrl-P works without sleep.
        nvim.feedkeys(ctrl_p, 'nt')
    elif method == 'bs':
        # XXX: deoplete needs sleep here.
        pass
    elif method == 'esc+C':
        # this works.
        nvim.feedkeys(esc)
        nvim.feedkeys('C')

    wait_until(lambda: nvim.eval('pumvisible()'))


def test_800(setup_buffer, nvim: Nvim,
             request: _pytest.fixtures.FixtureRequest,
             # neovim_logger: logging.Logger,
             ):
    """https://github.com/Shougo/deoplete.nvim/issues/800

    Fixes in https://github.com/Shougo/deoplete.nvim/commit/1fe1e88f
    """
    esc = nvim.replace_termcodes(r'<esc>')

    nvim.command('call deoplete#enable()')

    nvim.feedkeys('A')
    wait_until(lambda: nvim.eval('pumvisible()'))

    nvim.feedkeys('n')
    wait_until(lambda: nvim.eval('!pumvisible()'))
    # request.getfixturevalue('neovim_logger')

    # XXX: should not be necessary really, see above test which focuses on it
    # more.
    time.sleep(0.1)

    bs = nvim.replace_termcodes('<bs>')
    nvim.feedkeys(bs)
    wait_until(lambda: nvim.eval('pumvisible()'))

    nvim.feedkeys(esc, 'nt')
    wait_until(lambda: nvim.eval('!pumvisible()'))

    nvim.feedkeys('A', 'nt')
    wait_until(lambda: nvim.eval('pumvisible()'))
    # nvim.feedkeys(ctrl_p, 'nt')
