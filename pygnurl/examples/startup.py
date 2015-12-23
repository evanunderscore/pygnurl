"""Startup script giving history and completion.

Set PYTHONSTARTUP to the path to this file.
"""


def startup():
    """Perform startup tasks without cluttering the interpreter's
    global namespace.
    """
    import os
    import sys

    def register_readline():
        """Initialise readline history and completion.

        This function was taken from Python 3.5.0 with minor changes
        so it runs on older versions (readline raises IOError which was
        merged with OSError in 3.3, so we need to adjust references to
        OSError to check for IOError instead).

        >>> import inspect
        >>> import sys
        >>> source = inspect.getsource(sys.__interactivehook__)
        >>> source = source.replace('OSError', 'IOError')
        >>> print(source)
        """
        import atexit
        try:
            import readline
            import rlcompleter
        except ImportError:
            return

        # Reading the initialization (config) file may not be enough to set a
        # completion key, so we set one first and then read the file.
        readline_doc = getattr(readline, '__doc__', '')
        if readline_doc is not None and 'libedit' in readline_doc:
            readline.parse_and_bind('bind ^I rl_complete')
        else:
            readline.parse_and_bind('tab: complete')

        try:
            readline.read_init_file()
        except IOError:
            # An IOError here could have many causes, but the most likely one
            # is that there's no .inputrc file (or .editrc file in the case of
            # Mac OS X + libedit) in the expected location.  In that case, we
            # want to ignore the exception.
            pass

        if readline.get_current_history_length() == 0:
            # If no history was loaded, default to .python_history.
            # The guard is necessary to avoid doubling history size at
            # each interpreter exit when readline was already configured
            # through a PYTHONSTARTUP hook, see:
            # http://bugs.python.org/issue5845#msg198636
            history = os.path.join(os.path.expanduser('~'),
                                   '.python_history')
            try:
                readline.read_history_file(history)
            except IOError:
                pass
            atexit.register(readline.write_history_file, history)

    # This is duplicating work that newer versions of Python handle
    # automatically; only call this if it's not going to be handled for
    # us.
    if not hasattr(sys, '__interactivehook__'):
        register_readline()


# When running as the startup file, run the function and clean up.
if __name__ == '__main__':
    startup()
    del startup
    del __doc__  # pylint: disable=redefined-builtin
