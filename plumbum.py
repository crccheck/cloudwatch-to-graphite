# -*- coding: UTF-8 -*-
"""
Usage:
  plumbum <template> <namespace> [options]...

Examples:

  plumbum elb.yaml.j2 elb
  plumbum ec2.yaml.j2 ec2 environment=production

Outputs to stdout.

"""
from __future__ import unicode_literals

import sys

import boto.ec2
import boto.ec2.elb
import boto.rds
import jinja2


def get_property_func(key):
    """
    Get the accessor function for an instance to look for `key`.

    Look for it as an attribute, and if that does not work, look to see if it
    is a tag.
    """
    def get_it(obj):
        try:
            return getattr(obj, key)
        except AttributeError:
            return obj.tags.get(key)
    return get_it


def filter_key(filter_args):
    def filter_instance(instance):
        return all([value == get_property_func(key)(instance)
            for key, value in filter_args.items()])
    return filter_instance


def lookup(instances, filter_by=None):
    if filter_by:
        return filter(filter_key(filter_by), instances)
    return instances


def get_options(input_args):
    filter_by_kwargs = {}
    for arg in input_args:
        if arg.startswith('-'):
            # ignore options
            continue
        if '=' in arg:
            key, value = arg.split('=', 2)
            filter_by_kwargs[key] = value
    return filter_by_kwargs


def list_ec2(filter_by_kwargs):
    conn = boto.ec2.connect_to_region('us-east-1')  # XXX magic constant
    instances = conn.get_only_instances()
    return lookup(instances, filter_by=filter_by_kwargs)


def list_elb(filter_by_kwargs):
    conn = boto.ec2.elb.connect_to_region('us-east-1')  # XXX magic constant
    instances = conn.get_all_load_balancers()
    return lookup(instances, filter_by=filter_by_kwargs)


def list_rds(filter_by_kwargs):
    conn = boto.rds.connect_to_region('us-east-1')
    instances = conn.get_all_dbinstances()
    return lookup(instances, filter_by=filter_by_kwargs)


def main():
    if len(sys.argv) < 3:
        print __doc__
        sys.exit()
    options = sys.argv[1:]
    template = options[0]
    namespace = options[1].lower()
    filters = get_options(options[2:])

    # get the template first so this can fail before making a network request
    loader = jinja2.FileSystemLoader('.')
    jinja2_env = jinja2.Environment(loader=loader)
    template = jinja2_env.get_template(template)

    # should I be using ARNs?
    if namespace in ('ec2', 'aws/ec2'):
        resources = list_ec2(filters)
    elif namespace in ('elb', 'aws/elb'):
        resources = list_elb(filters)
    elif namespace in ('rds', 'aws/rds'):
        resources(filters)
    else:
        # TODO
        sys.exit(1)

    print template.render({
        'filters': filters,
        'resources': resources,
    })


if __name__ == '__main__':
    main()
