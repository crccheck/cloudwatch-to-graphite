# -*- coding: UTF-8 -*-
"""
Tests for Cloudwatch to Graphite (leadbutt)

WISHLIST: supress chatty stderr and stdout in tests
"""
from __future__ import unicode_literals

import unittest

import plumbum


class get_cli_optionsTest(unittest.TestCase):
    def test_trivial_case(self):
        argv = []
        with self.assertRaises(IndexError):
            plumbum.get_cli_options(argv)

    def test_minimal(self):
        argv = ['foo.j2', 'ec2']
        templ, ns, region, filter_by, extras = plumbum.get_cli_options(argv)
        self.assertEqual(templ, 'foo.j2')
        self.assertEqual(ns, 'ec2')
        self.assertEqual(region, plumbum.DEFAULT_REGION)
        self.assertFalse(len(filter_by))
        self.assertFalse(len(extras))

    def test_region_can_be_specified(self):
        argv = ['foo.j2', 'ec2', 'avengers-west-2']
        templ, ns, region, filter_by, extras = plumbum.get_cli_options(argv)
        self.assertEqual(templ, 'foo.j2')
        self.assertEqual(ns, 'ec2')
        self.assertEqual(region, 'avengers-west-2')
        self.assertFalse(len(filter_by))
        self.assertFalse(len(extras))


if __name__ == '__main__':
    unittest.main()
