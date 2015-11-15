"""Utility functions intended for internal use"""

import os
import logging
import warnings

from . import readline


READLINE_FUNCTION_NAMES = [
    'parse_and_bind',
    'get_line_buffer',
    'insert_text',
    'read_init_file',
    'read_history_file',
    'write_history_file',
    'clear_history',
    'get_history_length',
    'set_history_length',
    'get_current_history_length',
    'get_history_item',
    'remove_history_item',
    'replace_history_item',
    'redisplay',
    'set_startup_hook',
    'set_pre_input_hook',
    'set_completer',
    'get_completer',
    'get_completion_type',
    'get_begidx',
    'get_endidx',
    'set_completer_delims',
    'get_completer_delims',
    'set_completion_display_matches_hook',
    'add_history'
]


def init_logging(name):
    """Initialise debug logging

    :param name: Name to give to the logger (use __name__)
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

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
        logger.addHandler(file_handler)


def init_readline():
    """Initialise readline and return a dict containing required functions"""
    try:
        dll_path = os.environ['PYGNURL_DLL']
    except KeyError:
        # issue a warning to explain the error more clearly
        warnings.warn('pygnurl: PYGNURL_DLL environment variable not set',
                      RuntimeWarning, 2)
        raise
    instance = readline.Readline(dll_path)
    function_dict = {}
    for name in READLINE_FUNCTION_NAMES:
        function_dict[name] = getattr(instance, name)
    return function_dict
