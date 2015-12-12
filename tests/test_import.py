"""Tests for importing pygnurl."""
import os
import sys
import unittest


class TestPygnurl(unittest.TestCase):
    # pylint: disable=missing-docstring
    def setUp(self):
        self.pygnurl_lib = None
        try:
            self.pygnurl_lib = os.environ['PYGNURL_LIB']
            del os.environ['PYGNURL_LIB']
        except KeyError:
            pass
        # Purge pygnurl from sys.modules so we can test imports.
        for module in list(sys.modules.keys()):
            if module == 'pygnurl' or module.startswith('pygnurl.'):
                del sys.modules[module]

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
            with self.assertRaisesRegexp(Exception, 'PYGNURL_LIB'):
                import pygnurl
