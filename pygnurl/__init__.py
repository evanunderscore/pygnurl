"""pygnurl: ctypes-based Python wrapper for GNU Readline"""
import importlib
import logging
import os
import sys


# This is working around a bug in Python's import machinery that
# appears to have been fixed in Python 3.5. If importing this the first
# time fails (which will be the case if the user forgets to set
# PYGNURL_LIB, for example), importing this a second time will trip the
# ImportError, even though these modules have been successfully
# imported. Since the first time this is imported is when the
# interpreter itself does it and it suppresses the traceback, the user
# will get no useful information unless I add in this workaround.
# See https://bugs.python.org/issue17716.
# pylint: disable=invalid-name
# from . import bindings
bindings = importlib.import_module('pygnurl.bindings')
# from . import errors
errors = importlib.import_module('pygnurl.errors')
# pylint: enable=invalid-name


def _init_logging():
    """Initialize logging.

    Other files should obtain subloggers using
    logging.getLogger(__name__).
    """
    logger = logging.getLogger(__name__)

    if '_PYGNURL_DEBUG' in os.environ:
        # Extremely verbose; intended for internal development only.
        logger.setLevel(logging.DEBUG)
    elif 'PYGNURL_DEBUG' in os.environ:
        # More useful for users writing callback functions.
        logger.setLevel(logging.INFO)
    else:
        # The end user won't want to see any messages at all.
        logger.setLevel(logging.CRITICAL)

    formatter = logging.Formatter('%(module)s.%(funcName)s: %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        filename = os.environ['_PYGNURL_LOGFILE']
    except KeyError:
        logger.debug('_PYGNURL_LOGFILE not set; not logging to file')
    else:
        logger.debug('using log file %s', filename)
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        # Can be as verbose as we like when logging to file.
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
_init_logging()


def _init_readline():
    """Return a Readline instance for the current platform."""
    if 'PYGNURL_LIB' not in os.environ:
        msg = 'PYGNURL_LIB environment variable not set'
        raise errors.ConfigurationError(msg)
    lib_filename = os.environ['PYGNURL_LIB']

    if sys.platform == 'win32':
        readline_class = bindings.WindowsReadline
    else:
        readline_class = bindings.Readline

    return readline_class(lib_filename)
readline = _init_readline()  # pylint: disable=invalid-name
