# -*- coding: UTF-8 -*-
"""
Tests for Cloudwatch to Graphite (leadbutt)

WISHLIST: supress chatty stderr and stdout in tests
"""
from __future__ import unicode_literals

from subprocess import call
import os
import unittest

import mock

import leadbutt


class get_configTest(unittest.TestCase):
    def test_example_config_loads(self):
        config = leadbutt.get_config('config.yaml.example')
        self.assertIn('metrics', config)

    @mock.patch('sys.stdin')
    def test_config_can_be_stdin(self, mock_stdin):
        # simulate reading stdin
        mock_stdin.read.side_effect = ['test: "123"\n', '']
        # mock_stdin.name = 'oops'
        config = leadbutt.get_config('-')
        self.assertIn('test', config)

    @mock.patch('sys.stdin')
    def test_config_handles_malformed_yaml(self, mock_stdin):
        mock_stdin.read.side_effect = ['-\nmalformed yaml', '']
        mock_stdin.name = 'oops'
        with self.assertRaises(SystemExit) as e:
            leadbutt.get_config('-')
        self.assertEqual(e.exception.code, 1)


@unittest.skipUnless('TOX_TEST_ENTRYPOINT' in os.environ,
    'This is only applicable if leadbutt is installed')
class mainTest(unittest.TestCase):
    def test_entry_point(self):
        # assert this does not raise an exception
        call(['leadbutt', '--help'])


if __name__ == '__main__':
    unittest.main()
