"""Exceptions raised by pygnurl."""


class PygnurlException(Exception):
    """Base class for exceptions raised by pygnurl."""
    pass


class ConfigurationError(PygnurlException):
    """pygnurl has not been correctly configured."""
    pass
