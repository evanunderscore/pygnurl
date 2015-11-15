# pygnurl

pygnurl is a ctypes-based Python wrapper for GNU Readline intended to be used
as a drop-in replacement for Python's built-in `readline` module. It is
currently intended for Windows Python which does not ship with a `readline`
module by default.

## Requirements

* 32-bit Python 2
* Readline DLL
    * http://gnuwin32.sourceforge.net/packages/readline.htm

Python 3 and 64-bit Readline should be supported in the near future.

## Quick Start Guide

```
git clone https://github.com/evanunderscore/pygnurl.git
pip install pygnurl\
set PYGNURL_DLL=X:\path\to\readline5.dll
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

[pyreadline] - Pure Python Readline implementation. (Windows)

[gnureadline] - Statically compiled GNU Readline Python module. (Mac OS X, Posix)

[pyreadline]: https://pypi.python.org/pypi/pyreadline
[gnureadline]: https://pypi.python.org/pypi/gnureadline
