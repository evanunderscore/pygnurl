"""Example showing custom functions in the interpreter.

Run using:
    PYTHONSTARTUP=<pygnurl>/examples/functions.py python
Or on Windows:
    set PYTHONSTARTUP=<pygnurl>/examples/functions.py
    python

This example binds the function to Meta-?, but you can reference the
function by name (show-signature) in your init file (~/.inputrc) and
bind it to a key combination of your choice.

For Windows users, the Meta key is ESC, so you must press ESC followed
by ? (which is Shift+/).

NOTE: This must be run from the startup file because show_signature
requires access to the interpreter globals in order to function
correctly.

This script leaks some things into the interpreter's namespace purely
for ease of testing; all code could be wrapped in a function that is
called then deleted as in startup.py.

Run help(show_signature) for more information.
"""
from __future__ import print_function

import pygnurl
import pygnurl.examples.startup


def show_signature(count, key):  # pylint: disable=unused-argument
    """Display the signature of the current function.

    Indended to be called from Readline.

    The point must be immediately after an opening bracket.

    >>> def foo(a, b=1, *c, **d):
    ...     pass
    ...
    >>> foo(# Press bound key combination here
        foo(a, b=1, *c, **d)
    >>> foo(
    """
    import pygnurl  # pylint: disable=redefined-outer-name,reimported

    line = pygnurl.readline.line_buffer
    index = pygnurl.readline.point - 1
    if line[index] != '(':
        raise Exception('not at start of function call')
    line = line[:index]
    name = ''
    for char in reversed(line):
        if char.isalnum() or char in ['_', '.']:
            name = char + name
        else:
            break
    if not name:
        raise Exception('could not find function name')
    func_or_class = eval(name, globals())  # pylint: disable=eval-used
    spec = _get_signature(func_or_class)
    padding = ' ' * (index - len(name) + len(pygnurl.readline.prompt))
    print('\n{}{}{}'.format(padding, name, spec))
    pygnurl.readline.forced_update_display()


def _get_signature(func_or_class):
    """Return a string of a function or class signature.

    Similar to inspect.signature, but works on older versions of
    Python and inspects the __init__ method of classes.
    """
    import inspect

    # pylint: disable=deprecated-method
    if inspect.isclass(func_or_class):
        spec = inspect.getargspec(func_or_class.__init__)
    else:
        spec = inspect.getargspec(func_or_class)

    defaults = spec.defaults or []
    if defaults:
        args = spec.args[:-len(defaults)]
        kwargs = spec.args[-len(defaults):]
    else:
        args = spec.args
        kwargs = []
    for name, value in zip(kwargs, defaults):
        args.append('{}={}'.format(name, value))
    if spec.varargs:
        args.append('*{}'.format(spec.varargs))
    if spec.keywords:
        args.append('**{}'.format(spec.keywords))
    return '({})'.format(', '.join(args))

pygnurl.readline.add_function('show-signature', show_signature)
pygnurl.readline.parse_and_bind(r'"\M-?": show-signature')

# We're overriding the sample startup script, so call that too.
pygnurl.examples.startup.startup()
