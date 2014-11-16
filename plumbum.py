# -*- coding: UTF-8 -*-
"""
Usage:
  plumbum <template> <namespace> [options]...

Examples:

  plumbum elb.yaml.j2 elb
  plumbum elb.yaml.j2 elb us-west-2
  plumbum ec2.yaml.j2 ec2 environment=production
  plumbum ec2.yaml.j2 ec2 us-west-2 environment=production

Outputs to stdout.

"""
from __future__ import unicode_literals

import sys

import boto
import boto.ec2
import boto.ec2.elb
import boto.rds
import jinja2


# DEFAULT_NAMESPACE = 'ec2'  # TODO
DEFAULT_REGION = 'us-east-1'


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


def get_cli_options(options):
    # template always has to be index 0
    template = options[0]
    # namespace always has to be index 1
    namespace = options[1].lower()
    # region might be index 2
    region = ''
    if len(options) < 3 or '=' in options[2]:
        next_idx = 2
    else:
        region = options[2]
        next_idx = 3
    region = region or boto.config.get('Boto', 'ec2_region_name', 'us-east-1')

    filter_by = {}
    extras = []
    for arg in options[next_idx:]:
        if arg.startswith('-'):
            extras.append(arg)
        elif '=' in arg:
            key, value = arg.split('=', 2)
            filter_by[key] = value
        else:
            extras.append(arg)

    return template, namespace, region, filter_by, extras


def list_ec2(region, filter_by_kwargs):
    conn = boto.ec2.connect_to_region(region)
    instances = conn.get_only_instances()
    return lookup(instances, filter_by=filter_by_kwargs)


def list_elb(region, filter_by_kwargs):
    conn = boto.ec2.elb.connect_to_region(region)
    instances = conn.get_all_load_balancers()
    return lookup(instances, filter_by=filter_by_kwargs)


def list_rds(region, filter_by_kwargs):
    conn = boto.rds.connect_to_region(region)
    instances = conn.get_all_dbinstances()
    return lookup(instances, filter_by=filter_by_kwargs)


def main():
    if len(sys.argv) < 3:
        print __doc__
        sys.exit()

    template, namespace, region, filters, __ = get_cli_options(sys.argv[1:])

    # get the template first so this can fail before making a network request
    loader = jinja2.FileSystemLoader('.')
    jinja2_env = jinja2.Environment(loader=loader)
    template = jinja2_env.get_template(template)

    # insure a valid region is set
    if not region in [r.name for r in boto.ec2.regions()]:
        raise ValueError("Invalid region:{0}".format(region))

    # should I be using ARNs?
    if namespace in ('ec2', 'aws/ec2'):
        resources = list_ec2(region, filters)
    elif namespace in ('elb', 'aws/elb'):
        resources = list_elb(region, filters)
    elif namespace in ('rds', 'aws/rds'):
        resources = list_rds(region, filters)
    else:
        # TODO
        sys.exit(1)

    print template.render({
        'filters': filters,
        'resources': resources,
        'region': region,       # Use for Auth config section if needed
    })


if __name__ == '__main__':
    main()
