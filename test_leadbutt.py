# -*- coding: UTF-8 -*-
"""
Tests for Cloudwatch to Graphite (leadbutt)

WISHLIST: supress chatty stderr and stdout in tests
"""
from __future__ import unicode_literals

from subprocess import call
import datetime
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

    @mock.patch('sys.stderr')
    @mock.patch('sys.stdin')
    def test_config_handles_malformed_yaml(self, mock_stdin, mock_stderr):
        mock_stdin.read.side_effect = ['-\nmalformed yaml', '']
        mock_stdin.name = 'oops'
        with self.assertRaises(SystemExit) as e:
            leadbutt.get_config('-')
        self.assertEqual(e.exception.code, 1)
        self.assertTrue(mock_stderr.write.called)


class output_results(unittest.TestCase):
    @mock.patch('sys.stdout')
    def test_default_formatter_used(self, mock_sysout):
        mock_results = [{
            'Timestamp': datetime.datetime.utcnow(),
            'Sum': 1337.0,
        }]
        metric = {
            'Namespace': 'AWS/Foo',
            'MetricName': 'RequestCount',
            'Statistics': 'Sum',
            'Unit': 'Count',
            'Dimensions': {'Krang': 'X'},
        }
        leadbutt.output_results(mock_results, metric)
        self.assertTrue(mock_sysout.write.called)
        out = mock_sysout.write.call_args[0][0]
        name, value, timestamp = out.split()
        # assert default formatter was used
        self.assertEqual(name, 'cloudwatch.aws.foo.x.requestcount.sum.count')
        self.assertEqual(value, '1337.0')

    @mock.patch('sys.stdout')
    def test_custom_formatter_used(self, mock_sysout):
        mock_results = [{
            'Timestamp': datetime.datetime.utcnow(),
            'Sum': 1337.0,
        }]
        metric = {
            'Namespace': 'AWS/Foo',
            'MetricName': 'RequestCount',
            'Statistics': 'Sum',
            'Unit': 'Count',
            'Dimensions': {'Krang': 'X'},
            'Options': {'Formatter': 'tmnt.%(dimension)s'}
        }
        leadbutt.output_results(mock_results, metric)
        self.assertTrue(mock_sysout.write.called)
        out = mock_sysout.write.call_args[0][0]
        name, value, timestamp = out.split()
        # assert custom formatter was used
        self.assertEqual(name, 'tmnt.x')
        self.assertEqual(value, '1337.0')

    @mock.patch('sys.stdout')
    def test_multiple_statistics_get_multiple_lines(self, mock_sysout):
        mock_results = [{
            'Timestamp': datetime.datetime.utcnow(),
            'Maximum': 9001.0,
            'Average': 1337.0,
        }]
        metric = {
            'Namespace': 'AWS/Foo',
            'MetricName': 'RequestCount',
            'Statistics': ['Maximum', 'Average'],
            'Unit': 'Count',
            'Dimensions': {'Krang': 'X'},
        }
        leadbutt.output_results(mock_results, metric)

        self.assertEqual(
            mock_sysout.write.call_count, len(metric['Statistics']))


@unittest.skipUnless('TOX_TEST_ENTRYPOINT' in os.environ,
    'This is only applicable if leadbutt is installed')
class mainTest(unittest.TestCase):
    def test_entry_point(self):
        # assert this does not raise an exception
        call(['leadbutt', '--help'])


if __name__ == '__main__':
    unittest.main()
