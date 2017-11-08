=======
pygnurl
=======

**Disclaimer:** This project is no longer maintained. I do not intend to add
any new features or fix bugs in 1.x. I *may* fix bugs in 0.8.x if requested.

``pygnurl`` is a dynamic GNU Readline interface. It provides:

- A Pythonic interface similar to ``rl`` for ease of use
- An interface to custom bindable functions
- A ``readline`` compatibility layer for existing code

You should use ``pygnurl`` if you specifically want to use GNU Readline from
your Python program. If you are just looking for tools to help you build a
command line interface, you may prefer prompt_toolkit_.

Requirements
------------

``pygnurl`` dynamically loads a Readline library, so you need a version
matching the architecture of your Python interpreter (not necessarily your
system).

Linux users should already have Readline as part of the standard library.
``pygnurl`` uses this version by default.

Windows users can get a pre-built 32-bit Readline DLL from `gnuwin32
<http://gnuwin32.sourceforge.net/packages/readline.htm>`_.

More information on where to get Readline can be found on the `Readline home
page <http://tiswww.case.edu/php/chet/readline/rltop.html#Availability>`_.

Quick Start Guide
-----------------

Install ``pygnurl`` using ``pip install pygnurl``.

Set the ``PYGNURL_LIB`` environment variable to the filename of your Readline
library. This will be loaded using the shared library search order rules of
your system. (Linux users can skip this step to use the system version).

If your version of Python already has a ``readline`` module, you will need to
do one of the following things to let ``pygnurl`` override it:

#. Add ``<site-packages>/pygnurl/modules`` to your ``PYTHONPATH`` environment
   variable
#. Install using ``easy_install`` instead of ``pip``

If you are using Python 3.4 or later, completion and history will be set up for
you automatically. If you are using an older version, you will need to set this
up yourself.

::

    >>> import rlcompleter
    >>> import readline
    >>> readline.parse_and_bind('tab: complete')
    >>> r<tab><tab>

Examples
--------

``pygnurl/examples/startup.py`` - An example startup file suitable for everyday
use. Point the ``PYTHONSTARTUP`` environment variable at this file to
automatically get tab completion and saved history in your interpreter. (If you
are using Python 3.4 or later, you do not need to use this example.)

``pygnurl/examples/functions.py`` - An example startup file demostrating a
custom bindable command. You must also use this with the ``PYTHONSTARTUP``
environment variable. Run ``help(pygnurl.examples.functions)`` for more
information.

``pygnurl/examples/mycmd.py`` - A simple command line showing tab completion
capabilities. The argument to ``cat`` is completed based on your local
filesystem.

Motivation
----------

``pygnurl`` aims to provide full GNU Readline support across all platforms with
no compilation overhead. Any pre-built Readline library should be able to be
dropped in with no code modifications. If necessary, version- or
platform-specific compatibility fixes can be implemented in Python, not C.

Development
-----------

For source code, questions and bug reports, visit the GitHub repository:

https://github.com/evanunderscore/pygnurl

Alternatives
------------

readline_ - Part of the standard library. Python on Mac OS X may implement this
using libedit instead of GNU Readline and must be configured accordingly.

pyreadline_ - A python implmentation of GNU readline.

gnureadline_ - The standard Python readline extension statically linked against
the GNU readline library.

rl_ - Alternative Python bindings for GNU Readline.

prompt_toolkit_ - Library for building powerful interactive command lines in
Python.

+-------------------+-----------+---------------+---------------+
|                   | Platforms | Library       | Interface     |
+===================+===========+===============+===============+
| pygnurl_          | Any       | Dynamic       | Extended      |
+-------------------+-----------+---------------+---------------+
| readline_         | Unix-like | Static        | Basic         |
+-------------------+-----------+---------------+---------------+
| pyreadline_       | Windows   | Pure Python   | Basic         |
+-------------------+-----------+---------------+---------------+
| gnureadline_      | Unix-like | Static        | Basic         |
+-------------------+-----------+---------------+---------------+
| rl_               | Unix-like | Static        | Extended      |
+-------------------+-----------+---------------+---------------+
| prompt_toolkit_   | Any       | Pure Python   | Alternative   |
+-------------------+-----------+---------------+---------------+

Known Bugs
----------

- ANSI color codes in the IPython terminal are not able to be printed. As a
  workaround, the codes are stripped and a plain prompt is displayed instead.
- libreadline6 from MinGW lags behind one keystroke when using the arrow keys.
  This appears to be related to the Readline callback interface.

.. _pygnurl: https://pypi.python.org/pypi/pygnurl
.. _readline: https://docs.python.org/3/library/readline.html
.. _pyreadline: https://pypi.python.org/pypi/pyreadline
.. _gnureadline: https://pypi.python.org/pypi/gnureadline
.. _rl: https://pypi.python.org/pypi/rl
.. _prompt_toolkit: https://pypi.python.org/pypi/prompt_toolkit
