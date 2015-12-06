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

setup()
del setup
