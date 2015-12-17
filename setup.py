#!/usr/bin/env python2
"""Packaging script for pygnurl."""

from setuptools import setup


def get_long_description():
    """Return the contents of README.rst."""
    with open('README.rst') as readme:
        return readme.read()


setup(
    name='pygnurl',
    version='0.8.0',
    description='ctypes-based Python wrapper for GNU Readline',
    long_description=get_long_description(),
    author='evanunderscore',
    author_email='evanunderscore@gmail.com',
    url='https://pypi.python.org/pypi/pygnurl',
    license='GNU General Public License v2',
    packages=['pygnurl', 'pygnurl.modules', 'pygnurl.scripts'],
    py_modules=['readline'],
    extras_require={
        ':sys_platform=="win32"': ['colorama>=0.3.5'],
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
    ],
    keywords='gnu readline bindings',
)
