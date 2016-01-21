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
        self.assertIn('Metrics', config)

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

    @mock.patch('sys.stderr')
    def test_config_handles_missing_file(self, mock_stderr):
        with self.assertRaises(SystemExit) as e:
            leadbutt.get_config('whatever_the_default_config_is')
        self.assertEqual(e.exception.code, 2)
        self.assertTrue(mock_stderr.write.called)


class get_optionsTest(unittest.TestCase):
    def test_get_options_returns_right_option(self):
        # only have the defaults
        options = leadbutt.get_options(None, None, None)
        self.assertEqual(options['Period'], 1)
        self.assertEqual(options['Count'], 5)

        # config options were specified
        config_options = {
            'Period': 2,
        }
        options = leadbutt.get_options(config_options, None, None)
        self.assertEqual(options['Period'], 2)
        self.assertEqual(options['Count'], 5)

        # local_options were specified
        local_options = {
            'Period': 3,
        }
        options = leadbutt.get_options(config_options, local_options, None)
        self.assertEqual(options['Period'], 3)
        self.assertEqual(options['Count'], 5)

        # cli_options were specified
        cli_options = {
            'Period': 4,
            'Count': 10,
        }
        options = leadbutt.get_options(config_options, local_options, cli_options)
        self.assertEqual(options['Period'], 4)
        self.assertEqual(options['Count'], 10)


class output_resultsTest(unittest.TestCase):
    @mock.patch('sys.stdout')
    def test_default_formatter_used(self, mock_sysout):
        mock_results = [{
            'Timestamp': datetime.datetime.utcnow(),
            'Unit': 'Count',
            'Sum': 1337.0,
        }]
        metric = {
            'Namespace': 'AWS/Foo',
            'MetricName': 'RequestCount',
            'Statistics': 'Sum',
            'Unit': 'Count',
            'Dimensions': {'Krang': 'X'},
        }
        options = leadbutt.get_options(None, metric.get('Options'), None)
        leadbutt.output_results(mock_results, metric, options)
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
            'Unit': 'Count',
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
        options = leadbutt.get_options(None, metric.get('Options'), None)
        leadbutt.output_results(mock_results, metric, options)
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
            'Unit': 'Count',
        }]
        metric = {
            'Namespace': 'AWS/Foo',
            'MetricName': 'RequestCount',
            'Statistics': ['Maximum', 'Average'],
            'Unit': 'Count',
            'Dimensions': {'Krang': 'X'},
        }
        options = leadbutt.get_options(None, metric.get('Options'), None)
        leadbutt.output_results(mock_results, metric, options)

        self.assertEqual(
            mock_sysout.write.call_count, len(metric['Statistics']))


class leadbuttTest(unittest.TestCase):
    @mock.patch('boto.ec2.cloudwatch.connect_to_region')
    @mock.patch('leadbutt.get_config')
    def test_can_get_auth_from_config(self, mock_get_config, mock_connect):
        mock_get_config.return_value = {
            'Metrics': [],
            'Auth': {
                'aws_access_key_id': 'foo',
                'aws_secret_access_key': 'bar',
            }
        }
        leadbutt.leadbutt('dummy_config_file', 'dummy_cli_options')
        self.assertTrue(mock_connect.called)
        args, kwargs = mock_connect.call_args
        self.assertEqual(kwargs['aws_access_key_id'], 'foo')
        self.assertEqual(kwargs['aws_secret_access_key'], 'bar')


@unittest.skipUnless('TOX_TEST_ENTRYPOINT' in os.environ,
    'This is only applicable if leadbutt is installed')
class mainTest(unittest.TestCase):
    def test_entry_point(self):
        # assert this does not raise an exception
        call(['leadbutt', '--help'])


if __name__ == '__main__':
    unittest.main()
