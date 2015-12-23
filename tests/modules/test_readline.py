"""Simple tests for pygnurl.readline"""
from __future__ import print_function

import os
import sys
import tempfile
import unittest

import pygnurl
from pygnurl.modules import readline

# FUTURE: fix versions and run over all supported
LIB_PATH = os.environ['PYGNURL_LIB']
print('python: {}'.format(sys.version))
print('readline: {}'.format(LIB_PATH))


class TestReadline(unittest.TestCase):
    """Simple tests mostly checking nothing crashes."""
    # pylint: disable=missing-docstring,too-many-public-methods,invalid-name
    # pylint: disable=protected-access,no-self-use
    def setUp(self):
        handle, self.init_file_name = tempfile.mkstemp()
        os.close(handle)
        handle, self.history_file_name = tempfile.mkstemp()
        os.close(handle)

        # FUTURE: add way to reset buffer, point, etc.
        pygnurl.readline.line_buffer = ''
        pygnurl.readline.point = 0

    def tearDown(self):
        os.remove(self.init_file_name)
        os.remove(self.history_file_name)

    def test_parse_and_bind(self):
        readline.parse_and_bind('tab: complete')

    def test_get_line_buffer(self):
        pygnurl.readline.line_buffer = ''
        line_buffer = readline.get_line_buffer()
        self.assertEqual(line_buffer, '')

    def test_insert_text(self):
        pygnurl.readline.line_buffer = ''
        readline.insert_text('test')
        line_buffer = readline.get_line_buffer()
        self.assertEqual(line_buffer, 'test')

    def test_read_init_file(self):
        readline.read_init_file(self.init_file_name)
        readline.read_init_file()

        with self.assertRaises(IOError):
            readline.read_init_file('/dev/null/nothing')

    def test_read_history_file(self):
        readline.read_history_file(self.history_file_name)
        # not going to deal with ~/.history

        with self.assertRaises(IOError):
            readline.read_history_file('/dev/null/nothing')

    def test_write_history_file(self):
        readline.write_history_file(self.history_file_name)
        # not going to deal with ~/.history

        with self.assertRaises(IOError):
            readline.write_history_file('/dev/null/nothing')

        readline.set_history_length(1)
        readline.write_history_file(self.history_file_name)

    def test_clear_history(self):
        readline.clear_history()

    def test_get_history_length(self):
        readline.get_history_length()

    def test_set_history_length(self):
        readline.set_history_length(123)
        length = readline.get_history_length()
        self.assertEqual(length, 123)

    def test_get_current_history_length(self):
        readline.get_current_history_length()

    def test_get_history_item(self):
        readline.add_history('test get history item')
        length = readline.get_current_history_length()
        item = readline.get_history_item(length)
        self.assertEqual(item, 'test get history item')

        item = readline.get_history_item(length + 1)
        self.assertIsNone(item)

    def test_remove_history_item(self):
        readline.add_history('test')
        length = readline.get_current_history_length()
        readline.remove_history_item(0)
        new_length = readline.get_current_history_length()
        self.assertEqual(new_length, length - 1)

        with self.assertRaises(ValueError):
            readline.remove_history_item(-1)
        with self.assertRaises(ValueError):
            readline.remove_history_item(length)

    def test_replace_history_item(self):
        readline.add_history('test replace history item 1')
        readline.replace_history_item(0, 'test replace history item 2')
        # replace is 0-based and get is 1-based
        item = readline.get_history_item(1)
        self.assertEqual(item, 'test replace history item 2')

        with self.assertRaises(ValueError):
            readline.replace_history_item(-1, 'test')
        with self.assertRaises(ValueError):
            readline.replace_history_item(0xffff, 'test')

    def test_redisplay(self):
        readline.redisplay()

    def test_set_startup_hook(self):
        readline.set_startup_hook(lambda: None)
        readline.set_startup_hook()

    def test_set_pre_input_hook(self):
        readline.set_pre_input_hook(lambda: None)
        readline.set_pre_input_hook()

    def test_set_completer(self):
        readline.set_completer(self._completer)
        completions = pygnurl.readline.completion.completer('b', 0, 1)
        self.assertEqual(completions, ['bar', 'baz'])
        readline.set_completer()
        self.assertIsNone(pygnurl.readline.completion.completer)

    def _completer(self, text, state):
        """Simple completer with fixed possibilities."""
        assert text == 'b'
        if state == 0:
            return 'bar'
        elif state == 1:
            return 'baz'
        else:
            return None

    def test_get_completer(self):
        # pylint: disable=unused-argument,multiple-statements
        def test(prefix, index): pass
        readline.set_completer(test)
        completer = readline.get_completer()
        self.assertEqual(completer, test)
        readline.set_completer()
        completer = readline.get_completer()
        self.assertIsNone(completer)

    def test_get_completion_type(self):
        comp_type = readline.get_completion_type()
        self.assertEqual(comp_type, 0)

    def test_get_begidx(self):
        readline.get_begidx()

    def test_get_endidx(self):
        readline.get_endidx()

    def test_completer_delims(self):
        _ = readline.get_completer_delims()
        readline.set_completer_delims('123')
        delims = readline.get_completer_delims()
        self.assertEqual(delims, '123')

    def test_set_completion_display_matches_hook(self):
        readline.set_completion_display_matches_hook(lambda x, y, z: None)
        readline.set_completion_display_matches_hook()

    def test_add_history(self):
        readline.add_history('test')

    def test_get_output_file(self):
        if sys.platform == 'win32':
            self.assertTrue(hasattr(readline.GetOutputFile(), 'write'))
        else:
            with self.assertRaises(NotImplementedError):
                readline.GetOutputFile()
