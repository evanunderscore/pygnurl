#!/usr/bin/env python2
"""Packaging script for pygnurl."""

from setuptools import setup


def get_long_description():
    """Return the contents of README.rst."""
    with open('README.rst') as readme:
        return readme.read()


setup(
    name='pygnurl',
    version='1.0.0',
    description='Dynamic GNU Readline interface',
    long_description=get_long_description(),
    author='evanunderscore',
    author_email='evanunderscore@gmail.com',
    url='https://pypi.python.org/pypi/pygnurl',
    license='GNU General Public License v2',
    packages=['pygnurl', 'pygnurl.modules', 'pygnurl.examples'],
    py_modules=['readline'],
    extras_require={
        ':sys_platform=="win32"': ['colorama>=0.3.5'],
    },
    tests_require=[
        'coverage',
        'nose',
    ],
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
