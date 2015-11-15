"""Importing this module enables command line editing using GNU readline."""
import pygnurl.util

for name, func in pygnurl.util.init_readline().items():
    globals()[name] = func
    del name, func
del pygnurl.util
