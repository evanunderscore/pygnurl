=======
pygnurl
=======

``pygnurl`` is a ctypes-based Python wrapper for GNU Readline intended to be
used as a drop-in replacement for Python's built-in ``readline`` module. It is
currently intended for Windows (as Python on Windows comes without a
``readline`` module by default) and Mac OS X (as its ``readline`` module is
implemented using libedit, not GNU Readline).

``pygnurl`` works with 32- and 64-bit Python 2 and 3.

Requirements
------------

``pygnurl`` dynamically loads a Readline library, so you need a version
matching the architecture of your Python interpreter (not necessarily your
system).

More information on where to get Readline can be found on the Readline home
page:

http://tiswww.case.edu/php/chet/readline/rltop.html#Availability

Windows users can get a pre-built 32-bit Readline DLL from:

http://gnuwin32.sourceforge.net/packages/readline.htm

Quick Start Guide
-----------------

Set the ``PYGNURL_LIB`` environment variable to the filename of your Readline
library. This will be loaded using the shared library search order rules of
your system.

If your version of Python already has a ``readline`` module, you will need to
do one of the following things to let ``pygnurl`` override it:

#. Add ``<site-packages>/pygnurl/modules`` to your ``PYTHONPATH`` environment
   variable
#. Install using ``easy_install`` instead of ``pip``

::

    pip install pygnurl
    python
    >>> import rlcompleter
    >>> import readline
    >>> readline.parse_and_bind('tab: complete')
    >>> r<tab><tab>

If you set the ``PYTHONSTARTUP`` environment variable to a Python file, it will
be run every time you start the interpreter. An example startup file giving tab
completion and saved history is provided in ``pygnurl/scripts/startup.py``. You
can point the environment variable directly at this file, or you can copy it
elsewhere and modify it to suit your needs.

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

+---------------+-----------+---------------+---------------+
|               | Platforms | Library       | Interfaces    |
+===============+===========+===============+===============+
| pygnurl_      | Any       | Dynamic       | Subset        |
+---------------+-----------+---------------+---------------+
| readline_     | Unix-like | Static        | Subset        |
+---------------+-----------+---------------+---------------+
| pyreadline_   | Windows   | Pure Python   | Subset        |
+---------------+-----------+---------------+---------------+
| gnureadline_  | Unix-like | Static        | Subset        |
+---------------+-----------+---------------+---------------+
| rl_           | Unix-like | Static        | All           |
+---------------+-----------+---------------+---------------+

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
