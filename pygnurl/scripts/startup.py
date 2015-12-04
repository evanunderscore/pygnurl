"""Startup script giving history and completion.

Set PYTHONSTARTUP to the path to this file.
"""


def startup():
    """Perform startup tasks without cluttering the interpreter's
    global namespace."""
    try:
        import readline
    except Exception:  # pylint: disable=broad-except
        import warnings
        warnings.warn('pygnurl: Could not import readline', RuntimeWarning)
        return

    # Load the history file and register it to be written on exit.
    import atexit
    import os
    histfile = os.path.expanduser('~/.pyhist')
    try:
        readline.read_history_file(histfile)
    except IOError:
        # History file won't exist if this is the first run.
        pass
    atexit.register(readline.write_history_file, histfile)

    # Set up tab completion in the interpreter.
    import rlcompleter
    readline.parse_and_bind('tab: complete')

# When running as the startup file, run the function and clean up.
if __name__ == '__main__':
    startup()
    del startup
