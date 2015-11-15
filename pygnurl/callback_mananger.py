"""Callback management utilities"""
import collections
from ctypes import *  # pylint: disable=wildcard-import,unused-wildcard-import
import logging


class CallbackManager(object):
    """Manager for ctypes DLL hooks"""
    def __init__(self, dll):
        self.dll = dll
        self.hooks = collections.defaultdict(dict)
        self.logger = logging.getLogger(__name__)

    def install(self, name, func):
        """
        Install a callback function ensuring a reference is kept.
        :param name: name of function to install
        :param func: callback function to install
        """
        self.logger.debug('installing callback for %s in %s', name, self.dll)
        self._install(name, func)

    def uninstall(self, name):
        """
        Remove an installed callback function.
        :param name: name of function to uninstall
        """
        self.logger.debug('uninstalling callback for %s in %s', name, self.dll)
        self._install(name)

    def _install(self, name, func=None):
        """Install or remove a callback function"""
        # install the callback function
        # pylint: disable=no-member
        c_void_p.in_dll(self.dll, name).value = cast(func, c_void_p).value
        # store the function so it doesn't get GC'd
        self.hooks[name] = func
