"""Tests for pygnurl.strings"""
from __future__ import unicode_literals

import sys
import unittest

import pygnurl.strings


class TestStrings(unittest.TestCase):
    """Test string conversion functions"""
    # pylint: disable=missing-docstring
    def test_encode(self):
        encoded = pygnurl.strings.encode('test')
        self.assertEqual(encoded, b'test')

    def test_encode_bytes(self):
        # This differs by version.
        raise NotImplementedError

    def test_encode_int(self):
        with self.assertRaises(TypeError):
            pygnurl.strings.encode(1)

    def test_decode(self):
        # This differs by version.
        raise NotImplementedError

    def test_strip_ansi_from_bytes(self):
        ipython_prompt = b'\n\x01\x1b[0;32m\x02In [\x01\x1b[1;32m\x021' \
                         b'\x01\x1b[0;32m\x02]: \x01\x1b[0m\x02'
        prompt = pygnurl.strings.strip_ansi_from_bytes(ipython_prompt)
        self.assertEqual(prompt, b'\nIn [1]: ')


class TestStrings2(TestStrings):
    """Test string conversion functions for Python 2"""
    def test_encode_bytes(self):
        encoded = pygnurl.strings.encode(b'test')
        self.assertEqual(encoded, b'test')

    def test_decode(self):
        decoded = pygnurl.strings.decode(b'test')
        self.assertEqual(decoded, b'test')


class TestStrings3(TestStrings):
    """Test string conversion functions for Python 3"""
    def test_encode_bytes(self):
        with self.assertRaises(TypeError):
            pygnurl.strings.encode(b'test')

    def test_decode(self):
        decoded = pygnurl.strings.decode(b'test')
        self.assertEqual(decoded, 'test')

# Run the right test for the current version.
if sys.version_info.major == 2:
    del TestStrings3
else:
    del TestStrings2
del TestStrings
