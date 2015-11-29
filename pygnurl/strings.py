"""Simple string conversion utilities for Python 2 and 3."""
import sys

PY3 = sys.version_info.major == 3


def encode(unicode_or_bytes):
    """Encode a string as bytes

    Attempts to imitate the 's' format for PyArg_ParseTuple.

    Python 3 accepts unicode objects only, Python 2 accepts both string
    and unicode objects.

    :param unicode_or_bytes: object to encode
    """
    if PY3:
        allowed = (str,)
        name = 'str'
    else:
        allowed = (str, unicode)  # pylint: disable=undefined-variable
        name = 'string'
    if not isinstance(unicode_or_bytes, allowed):
        msg = 'must be {}, not {}'.format(name,
                                          type(unicode_or_bytes).__name__)
        raise TypeError(msg)
    # Python 2 accepts raw strings
    if not PY3 and isinstance(unicode_or_bytes, str):
        return unicode_or_bytes
    else:
        return unicode_or_bytes.encode()


def decode(bytes_or_str):
    """Decode a string as bytes or unicode

    Attempts to imitate the 's' format for Py_BuildValue.

    Python 3 converts the bytes object to unicode, Python 2 performs no
    conversion.

    :param bytes_or_str: object to decode
    """
    if bytes_or_str is None:
        return None
    elif PY3:
        return bytes_or_str.decode()
    else:
        return bytes_or_str
