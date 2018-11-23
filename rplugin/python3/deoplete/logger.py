# ============================================================================
# FILE: logger.py
# AUTHOR: Tommy Allen <tommy at esdf.io>
# License: MIT license
# ============================================================================
import sys
import time
import logging

from functools import wraps
from collections import defaultdict

log_format = '%(asctime)s %(levelname)-8s [%(process)d] (%(name)s) %(message)s'
log_message_cooldown = 0.5

root = logging.getLogger('deoplete')
root.propagate = False
init = False


def getLogger(name):
    """Get a logger that is a child of the 'root' logger.
    """
    return root.getChild(name)


def setup(vim, level, output_file=None):
    """Setup logging for Deoplete
    """
    global init
    if init:
        return
    init = True

    if output_file:
        formatter = logging.Formatter(log_format)
        handler = logging.FileHandler(filename=output_file)
        handler.setFormatter(formatter)
        handler.addFilter(DeopleteLogFilter(vim))
        root.addHandler(handler)

        level = str(level).upper()
        if level not in ('DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR',
                         'CRITICAL', 'FATAL'):
            level = 'DEBUG'
        root.setLevel(getattr(logging, level))

        try:
            import pkg_resources

            pynvim_version = pkg_resources.get_distribution('pynvim').version
        except Exception:
            pynvim_version = 'unknown'

        log = getLogger('logging')
        log.info('--- Deoplete Log Start ---')
        log.info('%s, Python %s, pynvim %s',
                 vim.call('deoplete#util#neovim_version'),
                 '.'.join(map(str, sys.version_info[:3])),
                 pynvim_version)

        if not vim.vars.get('deoplete#_logging_notified'):
            vim.vars['deoplete#_logging_notified'] = 1
            vim.call('deoplete#util#print_debug', 'Logging to %s' % (
                output_file))


def logmethod(func):
    """Decorator for setting up the logger in LoggingMixin subclasses.

    This does not guarantee that log messages will be generated.  If
    `LoggingMixin.is_debug_enabled` is True, it will be propagated up to the
    root 'deoplete' logger.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not init or not self.is_debug_enabled:
            return
        if self._logger is None:
            self._logger = getLogger(getattr(self, 'name', 'unknown'))
        return func(self, *args, **kwargs)
    return wrapper


class LoggingMixin(object):
    """Class that adds logging functions to a subclass.
    """
    is_debug_enabled = False
    _logger = None  # type: logging.Logger

    @logmethod
    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)

    @logmethod
    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    @logmethod
    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)
    warn = warning

    @logmethod
    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    @logmethod
    def exception(self, msg, *args, **kwargs):
        # This will not produce a log message if there is no exception to log.
        self._logger.exception(msg, *args, **kwargs)

    @logmethod
    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)
    fatal = critical


class DeopleteLogFilter(logging.Filter):
    def __init__(self, vim, name=''):
        self.vim = vim
        self.counter = defaultdict(int)
        self.last_message_time = 0
        self.last_message = None

    def filter(self, record):
        t = time.time()
        elapsed = t - self.last_message_time
        self.last_message_time = t

        message = (record.levelno, record.name, record.msg, record.args)
        if message == self.last_message and elapsed < log_message_cooldown:
            # Ignore if the same message comes in too fast.
            return False
        self.last_message = message

        if record.levelno >= logging.ERROR:
            self.counter[record.name] += 1
            if self.counter[record.name] <= 2:
                # Only permit 2 errors in succession from a logging source to
                # display errors inside of Neovim.  After this, it is no longer
                # permitted to emit any more errors and should be addressed.
                self.vim.call('deoplete#util#print_error', record.getMessage(),
                              record.name)
            if record.exc_info and record.stack_info:
                # Add a penalty for messages that generate exceptions to avoid
                # making the log harder to read with doubled stack traces.
                self.counter[record.name] += 1
        elif self.counter[record.name] < 2:
            # If below the threshold for silencing a logging source, reset its
            # counter.
            self.counter[record.name] = 0
        return True
