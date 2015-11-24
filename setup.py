#!/usr/bin/env python2

from setuptools import setup


def get_long_description():
    with open('README.rst') as readme:
        return readme.read()


setup(
    name='pygnurl',
    version='0.3.0',
    description='ctypes-based Python wrapper for GNU Readline',
    long_description=get_long_description(),
    author='evanunderscore',
    author_email='evanunderscore@gmail.com',
    url='https://pypi.python.org/pypi/pygnurl',
    license='GNU General Public License v2',
    packages=['pygnurl'],
    py_modules=['readline'],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        # FUTURE: switch to "OS Independent" when tested appropriately
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
    ],
    keywords='gnu readline bindings',
)
