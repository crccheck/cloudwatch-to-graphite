# -*- coding: UTF-8 -*-
"""
Tests for Cloudwatch to Graphite (leadbutt)

My class names are funny because I name them after the function they cover.
"""
from __future__ import unicode_literals

import unittest
import mock

import plumbum


class GetCLIOptionsTests(unittest.TestCase):  # flake8: noqa

    def test_all_args(self):
        args = [
            '-r', 'non-legal-region',
            'ec2',
            '-f', 'instance-type=c3.large',
            'foo.yaml.j2'
        ]
        templ, ns, region, filter_by, token = plumbum.interpret_options(args)

        self.assertEqual(region, 'non-legal-region')
        self.assertEqual(ns, 'ec2')
        self.assertEqual(templ, 'foo.yaml.j2')
        self.assertEqual(filter_by, 'instance-type=c3.large')

    def test_namespace_can_use_cloudwatch_syntax(self):
        args = [
            'AWS/EC2',
            'foo.yaml.j2'
        ]
        templ, ns, region, filter_by, token = plumbum.interpret_options(args)
        self.assertEqual(templ, 'foo.yaml.j2')
        self.assertEqual(ns, 'ec2')

    @mock.patch('plumbum.sys.exit')
    def test_no_template(self, mock_exit):
        """
        Test that if the namespace and template are not passed,
        we get the correct failure/exit.
        """
        args = [
            'ec2',
            '-f', 'instance-type=c3.large',
        ]
        templ, ns, region, filter_by, token = plumbum.interpret_options(args)
        self.assertEqual(templ, None)
        self.assertEqual(region, plumbum.DEFAULT_REGION)
        self.assertEqual(filter_by, 'instance-type=c3.large')


class ListXXXTests(unittest.TestCase):
    @mock.patch('boto.elasticache.connect_to_region')
    def test_list_elasticache_trivial_case(self, mock_boto):
        clusters = plumbum.list_elasticache('moo', None)
        self.assertEqual(clusters, [])

        clusters = plumbum.list_elasticache('moo', {})
        self.assertEqual(clusters, [])

    @mock.patch('boto.dynamodb.connect_to_region')
    def test_list_dynamodb_trivial_case(self, mock_boto):
        mock_boto.return_value.list_tables.return_value = []
        tables = plumbum.list_dynamodb('moo', None)
        self.assertEqual(tables, [])

        tables = plumbum.list_dynamodb('moo', {})
        self.assertEqual(tables, [])


if __name__ == '__main__':
    unittest.main()
