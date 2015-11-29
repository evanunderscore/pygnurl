"""Simple tests for pygnurl.readline"""
from __future__ import print_function

import os
import sys
import tempfile
import unittest

import pygnurl.readline

# FUTURE: fix versions and run over all supported
LIB_PATH = os.environ['PYGNURL_LIB']
print('python: {}'.format(sys.version))
print('readline: {}'.format(LIB_PATH))


class TestReadline(unittest.TestCase):
    """Simple tests mostly checking nothing crashes"""
    # pylint: disable=missing-docstring,too-many-public-methods,invalid-name
    def setUp(self):
        self.readline = pygnurl.readline.Readline(LIB_PATH)
        handle, self.init_file_name = tempfile.mkstemp()
        os.close(handle)
        handle, self.history_file_name = tempfile.mkstemp()
        os.close(handle)

    def tearDown(self):
        os.remove(self.init_file_name)
        os.remove(self.history_file_name)

    def test_parse_and_bind(self):
        self.readline.parse_and_bind('tab: complete')

    def test_get_line_buffer(self):
        line_buffer = self.readline.get_line_buffer()
        self.assertEqual(line_buffer, '')

    def test_insert_text(self):
        self.readline.insert_text('test')
        line_buffer = self.readline.get_line_buffer()
        self.assertEqual(line_buffer, 'test')

    def test_read_init_file(self):
        self.readline.read_init_file(self.init_file_name)
        self.readline.read_init_file()

    def test_read_history_file(self):
        self.readline.read_history_file(self.history_file_name)
        # not going to deal with ~/.history

    def test_write_history_file(self):
        self.readline.write_history_file(self.history_file_name)
        # not going to deal with ~/.history

    def test_clear_history(self):
        self.readline.clear_history()

    def test_get_history_length(self):
        self.readline.get_history_length()

    def test_set_history_length(self):
        self.readline.set_history_length(123)
        length = self.readline.get_history_length()
        self.assertEqual(length, 123)

    def test_get_current_history_length(self):
        self.readline.get_current_history_length()

    def test_get_history_item(self):
        self.readline.add_history('test get history item')
        length = self.readline.get_current_history_length()
        item = self.readline.get_history_item(length)
        self.assertEqual(item, 'test get history item')

    def test_remove_history_item(self):
        self.readline.add_history('test')
        length = self.readline.get_current_history_length()
        self.readline.remove_history_item(0)
        new_length = self.readline.get_current_history_length()
        self.assertEqual(new_length, length - 1)

    def test_replace_history_item(self):
        self.readline.add_history('test replace history item 1')
        self.readline.replace_history_item(0, 'test replace history item 2')
        # replace is 0-based and get is 1-based?
        item = self.readline.get_history_item(1)
        self.assertEqual(item, 'test replace history item 2')

    def test_redisplay(self):
        self.readline.redisplay()

    def test_set_startup_hook(self):
        self.readline.set_startup_hook(lambda: None)
        self.readline.set_startup_hook()

    def test_set_pre_input_hook(self):
        self.readline.set_pre_input_hook(lambda: None)
        self.readline.set_pre_input_hook()

    def test_set_completer(self):
        self.readline.set_completer(lambda x, y: None)
        self.readline.set_completer()

    def test_get_completer(self):
        def test(prefix, index):  # pylint: disable=unused-argument
            return None
        self.readline.set_completer(test)
        completer = self.readline.get_completer()
        self.assertEqual(completer, test)
        self.readline.set_completer()
        completer = self.readline.get_completer()
        self.assertIsNone(completer)

    def test_get_completion_type(self):
        self.readline.get_completion_type()

    def test_get_begidx(self):
        self.readline.get_begidx()

    def test_get_endidx(self):
        self.readline.get_endidx()

    def test_set_completer_delims(self):
        self.readline.set_completer_delims('abc')

    def test_get_completer_delims(self):
        self.readline.set_completer_delims('123')
        delims = self.readline.get_completer_delims()
        self.assertEqual(delims, '123')

    def test_set_completion_display_matches_hook(self):
        self.readline.set_completion_display_matches_hook(lambda x, y, z: None)
        self.readline.set_completion_display_matches_hook()

    def test_add_history(self):
        self.readline.add_history('test')
