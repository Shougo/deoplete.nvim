import json
import logging
import os
import sys

import neovim
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'rplugin/python3'))


@pytest.fixture
def neovim_logger():
    """Get Neovim's logger."""

    # TODO: logger/formatter should be set in neovim.logger/neovim.formatter
    # already.
    logger = logging.getLogger('neovim')
    handler = logging.StreamHandler()
    handler.formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s @ '
        '%(filename)s:%(funcName)s:%(lineno)s] %(process)s - %(message)s')

    logging.root.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    yield logger

    logging.root.removeHandler(handler)


# TODO: scope - could be session probably
@pytest.fixture
def nvim():
    """Bases on fixture from neovim-python-client's tests."""
    child_argv = os.environ.get('NVIM_CHILD_ARGV')
    listen_address = os.environ.get('NVIM_LISTEN_ADDRESS')
    if child_argv is None and listen_address is None:
        child_argv = '["nvim", "-u", "NONE", "--embed"]'

    if child_argv is not None:
        editor = neovim.attach('child', argv=json.loads(child_argv))
    else:
        editor = neovim.attach('socket', path=listen_address)

    vimrc = os.path.join(os.path.dirname(__file__), 'vimrc')
    editor.command('source %s' % (vimrc,))

    lines = editor.options['lines']
    columns = editor.options['columns']

    # NOTE: editor.ui_attach does not support options yet.
    # https://github.com/neovim/python-client/pull/345
    # editor.ui_attach(columns, lines, ext_popupmenu=True)
    opts = {'ext_popupmenu': True}
    editor.api.ui_attach(columns, lines, opts)

    return editor
