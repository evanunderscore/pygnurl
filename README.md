# pygnurl

`pygnurl` is a ctypes-based Python wrapper for GNU Readline intended to be used
as a drop-in replacement for Python's built-in `readline` module. It is
currently intended for Windows Python which does not ship with a `readline`
module by default.

`pygnurl` works with 32- and 64-bit Python 2 and 3.

## Requirements

`pygnurl` dynamically binds to a Readline DLL, so you need a DLL matching the
architecture of your Python interpreter (not necessarily your system). If you
are using 32-bit Python, you can get a pre-built Windows-compatible Readline
DLL from:

http://gnuwin32.sourceforge.net/packages/readline.htm

## Quick Start Guide

```
git clone https://github.com/evanunderscore/pygnurl.git
pip install pygnurl\
set PYGNURL_DLL=X:\path\to\readline.dll
setx PYGNURL_DLL %PYGNURL_DLL%
python
>>> import rlcompleter
>>> import readline
>>> readline.parse_and_bind('tab: complete')
>>> r<tab><tab>
```

If your Readline DLL is on your PATH, you can specify `PYGNURL_DLL` by name
only. Note that if you specify `PYGNURL_DLL` with a path, `pygnurl` won't be
able to load it if it depends on other DLLs not on your PATH.

## Motivation

`pygnurl` aims to provide full GNU Readline support across all platforms with
no compilation overhead. Any pre-built Readline library should be able to be
dropped in with no code modifications. If necessary, version- or
platform-specific compatibility fixes can be implemented in Python, not C.

## Alternatives

[pyreadline] - A python implmementation of GNU readline. (Windows)

[gnureadline] - The standard Python readline extension statically linked
against the GNU readline library. (Mac OS X, Posix)

[rl] - Alternative Python bindings for GNU Readline. (Linux, Mac OS X)

[pyreadline]: https://pypi.python.org/pypi/pyreadline
[gnureadline]: https://pypi.python.org/pypi/gnureadline
[rl]: https://pypi.python.org/pypi/rl
