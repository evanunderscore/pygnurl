"""Importing this module enables command line editing using GNU
readline.
"""


def _setup():
    """Populate the global namespace with readline functions.

    Imports are contained within this function to avoid cluttering the
    global namespace.
    """
    import sys

    import pygnurl

    attributes = [
        '_READLINE_VERSION',
        '_READLINE_RUNTIME_VERSION',
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

    for attr in attributes:
        globals()[attr] = getattr(pygnurl.readline, attr)

    if sys.platform == 'win32':
        # For IPython, fake pyreadline's GetOutputFile function.
        import colorama.initialise
        colorama.initialise.init()
        colorama.initialise.deinit()
        output_file = colorama.initialise.wrapped_stdout
        # colorama is proxying method calls using __getattr__ but
        # IPython.utils.io.IOStream is looking through the dir, so we
        # have to promote any proxied attributes to real ones.
        # pylint: disable=protected-access,no-member
        wrapped = output_file._StreamWrapper__wrapped
        for attr in dir(wrapped):
            if attr not in dir(output_file):
                proxied = getattr(output_file, attr)
                setattr(output_file, attr, proxied)
        globals()['GetOutputFile'] = lambda: output_file

_setup()
del _setup
