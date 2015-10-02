# -*- coding: UTF-8 -*-
"""
Tests for Cloudwatch to Graphite (leadbutt)
"""
from __future__ import unicode_literals

import unittest

import plumbum


class get_cli_optionsTest(unittest.TestCase):
    def test_trivial_case(self):
        argv = []
        with self.assertRaises(IndexError):
            plumbum.interpret_options(argv)

    def test_minimal(self):
        argv = ['foo.j2', 'ec2']
        templ, ns, region, filter_by, extras = plumbum.interpret_options(argv)
        self.assertEqual(templ, 'foo.j2')
        self.assertEqual(ns, 'ec2')
        self.assertEqual(region, plumbum.DEFAULT_REGION)
        self.assertFalse(len(filter_by))
        self.assertFalse(len(extras))

    def test_namespace_can_use_cloudwatch_syntax(self):
        argv = ['foo.j2', 'AWS/EC2']
        templ, ns, region, filter_by, extras = plumbum.interpret_options(argv)
        self.assertEqual(templ, 'foo.j2')
        self.assertEqual(ns, 'ec2')

    def test_region_can_be_specified(self):
        argv = ['foo.j2', 'ec2', 'avengers-west-2']
        templ, ns, region, filter_by, extras = plumbum.interpret_options(argv)
        self.assertEqual(templ, 'foo.j2')
        self.assertEqual(ns, 'ec2')
        self.assertEqual(region, 'avengers-west-2')
        self.assertFalse(len(filter_by))
        self.assertFalse(len(extras))

        # more regions
        argv = ['foo.j2', 'ec2', 'us-east-1']
        templ, ns, region, filter_by, extras = plumbum.interpret_options(argv)
        self.assertEqual(region, 'us-east-1')
        argv = ['foo.j2', 'ec2', 'cn-north-1']
        templ, ns, region, filter_by, extras = plumbum.interpret_options(argv)
        self.assertEqual(region, 'cn-north-1')
        argv = ['foo.j2', 'ec2', 'ap-northeast-1']
        templ, ns, region, filter_by, extras = plumbum.interpret_options(argv)
        self.assertEqual(region, 'ap-northeast-1')
        argv = ['foo.j2', 'ec2', 'us-gov-west-1']
        templ, ns, region, filter_by, extras = plumbum.interpret_options(argv)
        self.assertEqual(region, 'us-gov-west-1')

    def test_filters_and_extras_found(self):
        argv = ['foo.j2', 'ec2', 'bar=mars', '--whee', 'xyzzy']
        templ, ns, region, filter_by, extras = plumbum.interpret_options(argv)
        self.assertEqual(templ, 'foo.j2')
        self.assertEqual(ns, 'ec2')
        self.assertEqual(region, plumbum.DEFAULT_REGION)
        self.assertEqual(len(filter_by), 1)
        self.assertEqual(len(extras), 2)

    def test_filters_and_extras_with_region_specified(self):
        argv = ['foo.j2', 'ec2', 'avengers-west-2', 'bar=mars', '--whee', 'xyzzy']
        templ, ns, region, filter_by, extras = plumbum.interpret_options(argv)
        self.assertEqual(templ, 'foo.j2')
        self.assertEqual(ns, 'ec2')
        self.assertEqual(region, 'avengers-west-2')
        self.assertEqual(len(filter_by), 1)
        self.assertEqual(len(extras), 2)

    def test_dynamodb_namespace(self):
        argv = ['foo.j2', 'dynamodb', 'us-east-1']
        templ, ns, region, filter_by, extras = plumbum.interpret_options(argv)
        self.assertEqual(templ, 'foo.j2')
        self.assertEqual(ns, 'dynamodb')
        self.assertEqual(region, 'us-east-1')

if __name__ == '__main__':
    unittest.main()
