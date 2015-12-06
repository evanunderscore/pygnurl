"""Simple string conversion utilities for Python 2 and 3."""
import re
import sys

PY3 = sys.version_info.major >= 3
# Borrowed from colorama.ansitowin32.AnsiToWin32.ANSI_CSI_RE.
# (This one is always bytes.)
# pylint: disable=anomalous-backslash-in-string
ANSI_CSI_RE = re.compile(b'\001?\033\[((?:\d|;)*)([a-zA-Z])\002?')


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


def strip_ansi_from_bytes(text):
    """Strip any ANSI color codes from the text.

    This function is heavily borrowed from colorama.
    See colorama.ansitowin32.AnsiToWin32.write_and_convert.
    """
    stripped = b''
    cursor = 0
    matches = ANSI_CSI_RE.finditer(text)
    for match in matches:
        start, end = match.span()
        stripped += text[cursor:start]
        cursor = end
    stripped += text[cursor:]
    return stripped
