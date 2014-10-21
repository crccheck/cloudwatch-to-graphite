# -*- coding: UTF-8 -*-
"""
Usage:
  plumbum <template> <namespace> [options]

Examples:

  plumbum elb.html.j2 elb

"""
from __future__ import unicode_literals

from docopt import docopt
import boto.ec2
import boto.ec2.elb
import boto.rds


def get_property_func(key):
    """
    Get the accessor function for an instance to look for `key`.

    Look for it as an attribute, and if that does not work, look to see if it
    is a tag.
    """
    aliases = {
        'ip': 'ip_address',
        'private_ip': 'private_ip_address',
    }
    unaliased_key = aliases.get(key, key)

    def get_it(obj):
        try:
            return getattr(obj, unaliased_key)
        except AttributeError:
            if key == 'name':
                return obj.tags.get('Name')
            return obj.tags.get(key)
    return get_it


def filter_key(filter_args):
    def filter_instance(instance):
        return all([value == get_property_func(key)(instance)
            for key, value in filter_args.items()])
    return filter_instance


def voyeur(instances, to_row, sort_by=None, filter_by=None):
    if sort_by:
        instances.sort(key=get_property_func(sort_by))
    if filter_by:
        instances = filter(filter_key(filter_by), instances)  # XXX overwriting original
    return map(to_row, instances)


def get_options(input_args, headers=None):
    if headers is None:
        headers = ()
    sort_by = None  # WISHLIST have a tuple
    filter_by_kwargs = {}
    for arg in input_args:
        if arg.startswith('-'):
            # ignore options
            continue
        if '=' in arg:
            key, value = arg.split('=', 2)
            if key not in headers:
                exit('{} not valid'.format(key))
            filter_by_kwargs[key] = value
        elif arg in headers:
            sort_by = arg
        else:
            print 'skipped', arg
    return sort_by, filter_by_kwargs


def list_ec2(input_args):
    headers = (
        'name',
        'environment',
        'site',
        'ip',
        'private_ip',
        'launch_time',
        'id',
    )
    sort_by, filter_by_kwargs = get_options(input_args, headers)
    conn = boto.ec2.connect_to_region('us-east-1')  # XXX magic constant
    instances = conn.get_only_instances()
    to_row = lambda x: (
        x.tags.get('Name'),
        x.tags.get('environment'),
        x.tags.get('site'),
        x.ip_address,
        x.private_ip_address,
        x.launch_time.split('T', 2)[0],
        x.id,
    )
    print tabulate(
        voyeur(instances, to_row=to_row, sort_by=sort_by, filter_by=filter_by_kwargs),
        headers=headers)


def list_elb(input_args):
    headers = (
        'name',
        'dns_name',
        'pool',  # not queryable/sortable
        'created_time',
    )
    sort_by, filter_by_kwargs = get_options(input_args, headers)
    conn = boto.ec2.elb.connect_to_region('us-east-1')  # XXX magic constant
    instances = conn.get_all_load_balancers()
    to_row = lambda x: (
        x.name,
        x.dns_name,
        len(x.instances),
        x.created_time,
    )
    print tabulate(
        voyeur(instances, to_row=to_row, sort_by=sort_by, filter_by=filter_by_kwargs),
        headers=headers)


def list_rds(input_args):
    def to_row(x):
        """More complicated `to_row` to handle missing DBName attribute."""
        data = x.__dict__.copy()
        data['DBName'] = getattr(x, 'DBName', '???')
        return (
            x.id,
            '{engine}://{master_username}@{_address}:{_port}/{DBName}'.format(**data),
        )
    headers = (
        'id',
        # 'engine',
        'uri',  # derived
    )
    sort_by, filter_by_kwargs = get_options(input_args, headers)
    conn = boto.rds.connect_to_region('us-east-1')
    instances = conn.get_all_dbinstances()
    print tabulate(
        voyeur(instances, to_row=to_row, sort_by=sort_by, filter_by=filter_by_kwargs),
        headers=headers)


def main():
    options = docopt(__doc__)
    print options


if __name__ == '__main__':
    main()
