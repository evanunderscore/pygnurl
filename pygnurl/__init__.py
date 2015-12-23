"""pygnurl: Dynamic GNU Readline interface."""
import ctypes
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
try:
    from . import interface
    from . import errors
except ImportError:
    # pylint: disable=invalid-name
    interface = importlib.import_module('pygnurl.interface')
    errors = importlib.import_module('pygnurl.errors')

readline = None  # pylint: disable=invalid-name


class ConsoleHandler(logging.StreamHandler):
    """Readline-aware StreamHandler.

    Will add new lines and update display as required.
    """
    def format(self, record):
        """If accepting input, add a new line to the record."""
        msg = super(ConsoleHandler, self).format(record)
        if self._is_reading():
            msg = '\n' + msg
        return msg

    def emit(self, record):
        """If accepting input, update the display after logging."""
        super(ConsoleHandler, self).emit(record)
        if self._is_reading():
            readline.forced_update_display()

    @staticmethod
    def _is_reading():
        """Return True if Readline is currently reading a line."""
        # The logger may be written to before readline has been fully
        # initialized and assigned to this variable.
        return readline and not readline.done


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

    console_handler = ConsoleHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
_init_logging()


def _load_library():
    """Load and return the Readline shared library.

    The name is taken from the PYGNURL_LIB environment variable or a
    platform-specific default if one exists.
    """
    logger = logging.getLogger(__name__)

    try:
        environ_lib = os.environ['PYGNURL_LIB']
    except KeyError:
        pass
    else:
        logger.info('using environment library %s', environ_lib)
        return ctypes.cdll.LoadLibrary(environ_lib)

    default_lib = None
    if sys.platform.startswith('linux'):
        default_lib = 'libreadline.so.6'

    if default_lib is not None:
        logger.info('using default library %s', default_lib)
        try:
            return ctypes.cdll.LoadLibrary(default_lib)
        except OSError:
            logger.exception()

    msg = 'PYGNURL_LIB environment variable not set and no default found'
    raise errors.ConfigurationError(msg)


def _init_readline(dll):
    """Return a Readline instance for the current platform.

    :rtype: pygnurl.interface.Readline
    """
    if sys.platform == 'win32':
        return interface.WindowsReadline(dll)
    else:
        return interface.Readline(dll)
readline = _init_readline(_load_library())  # pylint: disable=invalid-name
