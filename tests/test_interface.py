"""Simple tests for pygnurl.readline"""
from __future__ import print_function

from ctypes import *  # pylint: disable=wildcard-import,unused-wildcard-import
import os
import sys
import tempfile
import unittest

try:
    from unittest import mock
except ImportError:
    import mock

import pygnurl.interface

# FUTURE: fix versions and run over all supported
LIB_PATH = os.environ['PYGNURL_LIB']
print('python: {}'.format(sys.version))
print('readline: {}'.format(LIB_PATH))

# pylint: disable=missing-docstring,invalid-name,protected-access


class TestReadline(unittest.TestCase):
    """Simple tests mostly checking nothing crashes."""
    def setUp(self):
        dll = cdll.LoadLibrary(LIB_PATH)
        self.readline = pygnurl.interface.Readline(dll)
        handle, self.init_file_name = tempfile.mkstemp()
        os.close(handle)

        # FUTURE: add way to reset buffer, point, etc.
        self.readline.line_buffer = ''
        self.readline.point = 0

    def tearDown(self):
        os.remove(self.init_file_name)

    def test_name(self):
        self.assertEqual(self.readline.name, 'python')

    def test_instream(self):
        self.readline.instream = 123
        self.assertEqual(self.readline.instream, 123)

    def test_outstream(self):
        self.readline.outstream = 456
        self.assertEqual(self.readline.outstream, 456)

    def test_done(self):
        self.readline.done = True
        self.assertTrue(self.readline.done)

    def test_point(self):
        self.readline.line_buffer = 'test'
        self.readline.point = len('test')
        self.assertEqual(self.readline.point, len('test'))

        with self.assertRaises(ValueError):
            self.readline.point = len('test') + 1

    def test_prompt(self):
        _ = self.readline.prompt

    def test_parse_and_bind(self):
        self.readline.parse_and_bind('tab: complete')

    def test_line_buffer(self):
        self.assertEqual(self.readline.line_buffer, '')
        self.readline.line_buffer = 'test'
        self.assertEqual(self.readline.line_buffer, 'test')

    def test_insert_text(self):
        self.assertEqual(self.readline.line_buffer, '')
        self.assertEqual(self.readline.point, 0)
        self.readline.insert_text('test1')
        self.assertEqual(self.readline.line_buffer, 'test1')
        self.assertEqual(self.readline.point, len('test1'))
        self.readline.insert_text('test3')
        self.assertEqual(self.readline.line_buffer, 'test1test3')
        self.assertEqual(self.readline.point, len('test1test3'))
        self.readline.point = len('test1')
        self.readline.insert_text('test2')
        self.assertEqual(self.readline.line_buffer, 'test1test2test3')
        self.assertEqual(self.readline.point, len('test1test2'))

    def test_delete_text(self):
        self.readline.line_buffer = 'test'
        self.readline.delete_text(0, len('test'))
        self.assertEqual(self.readline.line_buffer, '')
        self.assertEqual(self.readline.point, 0)

        self.readline.line_buffer = 'leading---trailing'
        self.readline.point = len('leading-')
        self.readline.delete_text(len('leading'), len('leading---'))
        self.assertEqual(self.readline.point, len('leading'))

        self.readline.line_buffer = 'leading---trailing'
        self.readline.point = len('leading---trail')
        self.readline.delete_text(len('leading'), len('leading---'))
        self.assertEqual(self.readline.point, len('leadingtrail'))

        self.readline.line_buffer = 'leading---trailing'
        self.readline.point = len('lead')
        self.readline.delete_text(len('leading'), len('leading---'))
        self.assertEqual(self.readline.point, len('lead'))

    def test_read_init_file(self):
        self.readline.read_init_file(self.init_file_name)
        self.readline.read_init_file()

        with self.assertRaises(IOError):
            self.readline.read_init_file('/dev/null/nothing')

    def test_redisplay(self):
        self.readline.redisplay()

    def test_forced_update_display(self):
        self.readline.forced_update_display()

    def test_startup_hook(self):
        self.readline.startup_hook = mock.Mock(return_value=123)
        self.assertEqual(self.readline._on_startup_hook(), 123)
        self.readline.startup_hook = None
        self.assertEqual(self.readline._on_startup_hook(), 0)
        self.readline.startup_hook = mock.Mock(side_effect=Exception)
        self.assertEqual(self.readline._on_startup_hook(), -1)

    def test_pre_input_hook(self):
        self.readline.pre_input_hook = mock.Mock(return_value=234)
        self.assertEqual(self.readline._on_pre_input_hook(), 234)
        self.readline.pre_input_hook = None
        self.assertEqual(self.readline._on_pre_input_hook(), 0)
        self.readline.pre_input_hook = mock.Mock(side_effect=Exception)
        self.assertEqual(self.readline._on_pre_input_hook(), -1)

    def test_add_function(self):
        function = mock.Mock()
        function.return_value = 789

        self.readline.add_function('test-function', function)
        ret = self.readline._function_wrappers[b'test-function'](123, 456)
        self.assertTrue(function.called_with(123, 456))
        self.assertEqual(ret, 789)

        # Adding function with same name doesn't make a new wrapper.
        self.readline.add_function('test-function', function)
        self.assertEqual(len(self.readline._function_wrappers), 1)

        ret = self.readline._on_function('no-function', 123, 456)
        self.assertEqual(ret, -1)


class TestHistory(unittest.TestCase):
    def setUp(self):
        dll = cdll.LoadLibrary(LIB_PATH)
        self.readline = pygnurl.interface.Readline(dll)
        self.history = self.readline.history
        self.readline.history.clear()
        handle, self.history_file_name = tempfile.mkstemp()
        os.close(handle)

    def tearDown(self):
        os.remove(self.history_file_name)

    def test_len(self):
        self.assertEqual(len(self.history), 0)
        self.history.append('test1')
        self.assertEqual(len(self.history), 1)
        self.history.append('test2')
        self.assertEqual(len(self.history), 2)

    def test_getitem(self):
        self.history.append('test1')
        self.assertEqual(self.history[0], 'test1')
        self.assertEqual(self.history[-1], 'test1')
        self.history.append('test2')
        self.assertEqual(self.history[0], 'test1')
        self.assertEqual(self.history[1], 'test2')
        self.assertEqual(self.history[-1], 'test2')
        self.assertEqual(self.history[-2], 'test1')
        with self.assertRaises(IndexError):
            _ = self.history[2]

    def test_setitem(self):
        self.history.append('test1')
        self.history.append('test2')
        self.history[0] = 'test3'
        self.assertEqual(self.history[0], 'test3')
        self.history[-1] = 'test4'
        self.assertEqual(self.history[1], 'test4')
        with self.assertRaises(IndexError):
            self.history[2] = 'test5'

    def test_delitem(self):
        self.history.append('test1')
        self.history.append('test2')
        self.history.append('test3')
        del self.history[1]
        self.assertEqual(len(self.history), 2)
        self.assertEqual(self.history[0], 'test1')
        self.assertEqual(self.history[1], 'test3')
        del self.history[-1]
        self.assertEqual(len(self.history), 1)
        self.assertEqual(self.history[0], 'test1')
        with self.assertRaises(IndexError):
            del self.history[1]

    def test_iter(self):
        for line in self.history:
            self.fail('history should be empty, found {}'.format(line))
        self.history.append('test1')
        self.history.append('test2')
        lines = []
        for line in self.history:
            lines.append(line)
        self.assertEqual(lines, ['test1', 'test2'])

    def test_pos(self):
        self.assertEqual(self.history.pos, 0)
        with self.assertRaises(IndexError):
            self.history.pos = 1
        self.history.append('test1')
        self.history.pos = 1
        with self.assertRaises(IndexError):
            self.history.pos = 2

    def test_read_file(self):
        self.readline.history.read_file(self.history_file_name)
        # not going to deal with ~/.history

        with self.assertRaises(IOError):
            self.readline.history.read_file('/dev/null/nothing')

    def test_write_file(self):
        self.readline.history.write_file(self.history_file_name)
        # not going to deal with ~/.history

        with self.assertRaises(IOError):
            self.readline.history.write_file('/dev/null/nothing')

    def test_truncate_file(self):
        self.history.append('test1')
        self.history.append('test2')
        self.history.write_file(self.history_file_name)
        self.history.truncate_file(1, self.history_file_name)
        self.history.clear()
        self.history.read_file(self.history_file_name)
        self.assertEqual(len(self.history), 1)

        with self.assertRaises(IOError):
            self.readline.history.truncate_file(1, '/dev/null/nothing')


class TestCompletion(unittest.TestCase):
    def setUp(self):
        dll = cdll.LoadLibrary(LIB_PATH)
        self.readline = pygnurl.interface.Readline(dll)
        self.completion = self.readline.completion
        self._start = 0
        self._end = 0

    def test_append_character(self):
        self.completion.append_character = 'a'
        self.assertEqual(self.completion.append_character, 'a')

    def test_suppress_append(self):
        self.completion.suppress_append = True
        self.assertTrue(self.completion.suppress_append)

    def test_word_break_characters(self):
        self.completion.word_break_characters = 'abc'
        self.assertEqual(self.completion.word_break_characters, 'abc')

    def test_basic_word_break_characters(self):
        _ = self.completion.basic_word_break_characters

    def test_type(self):
        self.assertEqual(self.completion.type, '\0')

    def test_quote_characters(self):
        self.completion.quote_characters = 'abc'
        self.assertEqual(self.completion.quote_characters, 'abc')

    def test_basic_quote_characters(self):
        _ = self.completion.basic_quote_characters

    def test_filename_quote_characters(self):
        self.completion.filename_quote_characters = 'abc'
        self.assertEqual(self.completion.filename_quote_characters, 'abc')

    def test_filename_completion_desired(self):
        self.completion.filename_completion_desired = True
        self.assertTrue(self.completion.filename_completion_desired)

    def test_completer(self):
        self.completion.completer = self._completer
        p_completions = self.completion._attempted_completion(b'b', 123, 456)
        self.assertEqual(self._start, 123)
        self.assertEqual(self._end, 456)
        completions = cast(p_completions, POINTER(c_char_p))
        self.assertEqual(completions[:4], [b'ba', b'bar', b'baz', None])

        # _attempted_completion is expected to allocate memory; free it
        completions = cast(p_completions, POINTER(c_void_p))
        for i in range(3):
            self.readline.lib.free(completions[i])
        self.readline.lib.free(p_completions)

        # pylint: disable=redefined-variable-type
        self.completion.completer = mock.Mock(side_effect=Exception)
        p_completions = self.completion._attempted_completion(b'b', 123, 456)
        self.assertIsNone(p_completions)

        self.completion.completer = None
        p_completions = self.completion._attempted_completion(b'b', 123, 456)
        self.assertIsNone(p_completions)

    def _completer(self, text, start, end):
        """Simple completer with fixed possibilities."""
        self._start = start
        self._end = end
        return [x for x in ['foo', 'bar', 'baz'] if x.startswith(text)]

    def test_completion_type(self):
        self.assertEqual(self.completion.type, '\0')

    def test_completion_display_matches_hook(self):
        hook = mock.Mock()
        self.completion.display_matches_hook = hook
        self.assertEqual(self.completion.display_matches_hook, hook)
        self.completion._on_display_matches_hook(['a', 'ab', 'ac'], 2, 123)
        hook.assert_called_with('a', ['ab', 'ac'], 123)

        self.completion.display_matches_hook = mock.Mock(side_effect=Exception)
        self.completion._on_display_matches_hook(['a', 'ab', 'ac'], 2, 123)

        self.completion.display_matches_hook = None
        self.assertIsNone(self.completion.display_matches_hook)

    def test_filename_completions(self):
        self.completion.filename_completions('')
