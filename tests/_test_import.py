"""Tests for importing pygnurl."""
import os
import sys
import unittest

import six

assert 'pygnurl' not in sys.modules, 'pygnurl already imported'


class TestPygnurl(unittest.TestCase):
    # pylint: disable=missing-docstring
    def setUp(self):
        self.pygnurl_lib = None
        self.pygnurl_lib = os.environ['PYGNURL_LIB']
        del os.environ['PYGNURL_LIB']

    def tearDown(self):
        # Restore the environment for any other tests.
        if self.pygnurl_lib is not None:
            os.environ['PYGNURL_LIB'] = self.pygnurl_lib

    def test_failed_import(self):
        """Test the module safely fails to import.

        See comment in pygnurl/__init__.py.
        """
        for _ in range(2):
            # Can't specifically catch the ConfigurationError because
            # we can't import it.
            with six.assertRaisesRegex(self, Exception, 'PYGNURL_LIB'):
                import pygnurl
