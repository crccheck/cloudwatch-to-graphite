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
            '-f', 'instance-type=c3.large',
            'foo.yaml.j2',
            'ec2',
        ]
        templ, ns, region, filter_by, token = plumbum.interpret_options(args)

        self.assertEqual(region, 'non-legal-region')
        self.assertEqual(ns, 'ec2')
        self.assertEqual(templ, 'foo.yaml.j2')
        self.assertEqual(filter_by, {u'instance-type': u'c3.large'})

    def test_namespace_can_use_cloudwatch_syntax(self):
        args = [
            'foo.yaml.j2',
            'AWS/EC2',
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
            '-f', 'instance-type=c3.large',
            'foo.yaml.j2',
        ]
        templ, ns, region, filter_by, token = plumbum.interpret_options(args)
        self.assertEqual(ns, None)
        self.assertEqual(region, plumbum.DEFAULT_REGION)
        self.assertEqual(filter_by, {u'instance-type': u'c3.large'})


class FilterTests(unittest.TestCase):

    # define 2 mock ec2 instances to test filters with
    instances= [mock.Mock(
        root_device_type=u'ebs',
        id=u'i-12345678',
        private_ip_address='10.4.3.2',
    ), mock.Mock(
        root_device_type=u'ebs',
        id=u'i-87654321',
        private_ip_address='10.5.4.3',
    )]

    # verify that you get the instance back from the filter
    def test_filter_hit(self):
        filter_args = {'root_device_type': 'ebs', 'private_ip_address': '10.4.3.2'}
        filtered_instances = plumbum.lookup(self.instances, filter_by=filter_args)
        self.assertEqual(1, len(filtered_instances))
        self.assertEqual(self.instances[0].id, filtered_instances[0].id)

    # verify that you *do not* get the instance back from the filter
    def test_filter_miss(self):
        filter_args = {'root_device_type': 'instance-store'}
        filtered_instances = plumbum.lookup(self.instances, filter_by=filter_args)
        self.assertEquals(0, len(filtered_instances))


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
