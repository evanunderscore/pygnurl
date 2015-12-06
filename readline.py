"""Importing this module enables command line editing using GNU readline."""


def setup():
    """Populate the global namespace with readline functions.

    Imports are contained within this function to avoid cluttering the
    global namespace.
    """
    import pygnurl.util

    for name, func in pygnurl.util.init_readline().items():
        globals()[name] = func

    import sys
    if sys.platform == 'win32':
        # For IPython, fake pyreadline's GetOutputFile function.
        import colorama.initialise
        colorama.initialise.init()
        colorama.initialise.deinit()
        output_file = colorama.initialise.wrapped_stdout
        globals()['GetOutputFile'] = lambda: output_file

setup()
del setup
