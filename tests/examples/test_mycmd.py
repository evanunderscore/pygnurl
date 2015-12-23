"""Simple tests for example shell."""
import os
import tempfile
import unittest

import pygnurl
import pygnurl.examples.mycmd

# pylint: disable=missing-docstring


class TestMyCmd(unittest.TestCase):
    def setUp(self):
        self.cmd = pygnurl.examples.mycmd.MyCmd()
        test_fd, self.test_filename = tempfile.mkstemp(prefix=__name__)
        os.write(test_fd, b'meow')
        os.close(test_fd)

    def tearDown(self):
        os.remove(self.test_filename)

    def test_do_cat(self):
        self.cmd.do_cat(self.test_filename)

    def test_complete_cat(self):
        _ = self.cmd.complete_cat('')

    def test_do_exit(self):
        self.assertEqual(self.cmd.do_exit(), 1)

    def test_complete(self):
        self.cmd.complete('', 0)
        self.assertEqual(pygnurl.readline.completion.append_character, ' ')
