Changelog
=========

1.0.0 (2016-02-06)
------------------

* Added Pythonic interface to Readline functions and variables
* Added Readline-aware logging handler

0.8.0 (2015-12-22)
------------------

* Added ``add_function`` for registering custom bindable functions
* Set minimum colorama version to prevent crashing bug on Windows

0.7.0 (2015-12-13)
------------------

* Reorganised package to expose the Readline instance at ``pygnurl.readline``
* Updated PYTHONSTARTUP script to deconflict with ``sys.__interactivehook__``

0.6.1 (2015-12-06)
------------------

* Fixed a bug where IPython printed a traceback after an output line on Windows
* Fixed compatibility with IPython on Python 3 on Windows

0.6.0 (2015-12-06)
------------------

* Added support for IPython

0.5.0 (2015-12-04)
------------------

* Added sample PYTHONSTARTUP script
* Fixed assorted minor bugs

0.4.1 (2015-12-02)
------------------

* Fixed a bug where Ctrl-C could crash callback functions

0.4.0 (2015-11-29)
------------------

* Added support for Linux and Mac OS X

0.3.0 (2015-11-25)
------------------

* Updated packaging scripts for release to PyPI

0.2.0 (2015-11-24)
------------------

* Added support for Python 3
* Added support for 64-bit Readline

0.1.0 (2015-11-22)
------------------

* Initial version
