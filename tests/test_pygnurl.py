"""Tests for the pygnurl module itself."""

import logging
import os
import unittest

import pygnurl

# pylint: disable=missing-docstring,protected-access


class TestConsoleHandler(unittest.TestCase):
    def setUp(self):
        self.handler = pygnurl.ConsoleHandler()
        self.record = logging.LogRecord('', 100, '', 1, 'test', [], None)

    def test_format(self):
        pygnurl.readline.done = True
        msg = self.handler.format(self.record)
        self.assertEqual(msg, 'test')

        pygnurl.readline.done = False
        msg = self.handler.format(self.record)
        self.assertEqual(msg, '\ntest')

    def test_emit(self):
        pygnurl.readline.done = True
        self.handler.emit(self.record)

        pygnurl.readline.done = False
        self.handler.emit(self.record)


class TestPygnurl(unittest.TestCase):
    def tearDown(self):
        del os.environ['PYGNURL_DEBUG']
        del os.environ['_PYGNURL_DEBUG']
        pygnurl._init_logging()

    def test_init_logging(self):
        log = logging.getLogger('pygnurl')

        pygnurl._init_logging()
        self.assertEqual(log.getEffectiveLevel(), logging.CRITICAL)

        os.environ['PYGNURL_DEBUG'] = '1'
        pygnurl._init_logging()
        self.assertEqual(log.getEffectiveLevel(), logging.INFO)

        os.environ['_PYGNURL_DEBUG'] = '1'
        pygnurl._init_logging()
        self.assertEqual(log.getEffectiveLevel(), logging.DEBUG)
