"""Tests for the bindable functions example."""
import ctypes
import unittest

import pygnurl
import pygnurl.examples.functions


class TestFunctions(unittest.TestCase):
    # pylint: disable=unused-argument,missing-docstring,protected-access
    # pylint: disable=multiple-statements
    def test_get_signature(self):
        def test1(one, two, *three): pass
        spec = pygnurl.examples.functions._get_signature(test1)
        self.assertEqual(spec, '(one, two, *three)')

        def test2(one, one1, two=1, two2=2, *three, **four): pass
        spec = pygnurl.examples.functions._get_signature(test2)
        self.assertEqual(spec, '(one, one1, two=1, two2=2, *three, **four)')

        def test3(one=1): pass
        spec = pygnurl.examples.functions._get_signature(test3)
        self.assertEqual(spec, '(one=1)')

    def test_get_signature_class(self):
        class Func(object):  # pylint: disable=too-few-public-methods
            def __init__(self, one1, two=1, two2=2, *three, **four): pass
        spec = pygnurl.examples.functions._get_signature(Func)
        self.assertEqual(spec, '(self, one1, two=1, two2=2, *three, **four)')

    def test_show_signature(self):
        def test1(): pass

        pygnurl.examples.functions.test1 = test1
        pygnurl.readline.lib.set(ctypes.c_char_p, 'rl_prompt', '>>> ')

        pygnurl.readline.line_buffer = 'a = test((test1(asdf'
        pygnurl.readline.point = 1
        with self.assertRaises(Exception):
            pygnurl.examples.functions.show_signature(0, 0)

        pygnurl.readline.point = len('a = test((')
        with self.assertRaises(Exception):
            pygnurl.examples.functions.show_signature(0, 0)

        pygnurl.readline.point = len('a = test((test1(')
        pygnurl.examples.functions.show_signature(0, 0)
