# -*- coding: UTF-8 -*-
"""
Usage:
  plumbum <template> <namespace> [region] [options]...

Options:
  template   path to the jinja2 template
  namespace  AWS namespace. Currently supports: elasticache, elb, ec2, rds, asg, sqs
  region     AWS region [default: us-east-1]
  options    key value combinations, they can be tags or any other property

Examples:

  plumbum elb.yaml.j2 elb
  plumbum elb.yaml.j2 elb us-west-2
  plumbum ec2.yaml.j2 ec2 environment=production
  plumbum ec2.yaml.j2 ec2 us-west-2 environment=production

Outputs to stdout.

About Templates:

Templates are used to generate config.yml files based on running resources.
They're written in jinja2, and have these variables available:

  filters    A dictionary of the filters that were passed in
  region     The region the resource is located in
  resources  A list of the resources as boto objects
"""
from __future__ import unicode_literals

import re
import sys

import boto
import boto.dynamodb
import boto.ec2
import boto.ec2.elb
import boto.rds
import boto.elasticache
import boto.ec2.autoscale
import boto.kinesis
import boto.sqs
import jinja2
import os.path

__version__ = '0.8.0'

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
    if filter_by is not None:
        return list(filter(filter_key(filter_by), instances))
    return instances


def interpret_options(options):
    """Parse all the command line options."""
    # template always has to be index 0
    template = options[0]
    # namespace always has to be index 1. Support 'ec2' (human friendly) and
    # 'AWS/EC2' (how CloudWatch natively calls these things)
    namespace = options[1].rsplit('/', 2)[-1].lower()
    next_idx = 2
    # region might be index 2
    region = ''
    if len(options) > 2 and re.match(r'^\w+\-[\w\-]+\-\d+$', options[2]):
        region = options[2]
        next_idx += 1
    else:
        next_idx = 2
    region = region or boto.config.get('Boto', 'ec2_region_name', 'us-east-1')

    filter_by = {}
    extras = []
    for arg in options[next_idx:]:
        if arg.startswith('-'):
            # throw these away for now
            extras.append(arg)
        elif '=' in arg:
            key, value = arg.split('=', 2)
            filter_by[key] = value
        else:
            # throw these away for now
            extras.append(arg)

    return template, namespace, region, filter_by, extras


def list_ec2(region, filter_by_kwargs):
    """List running ec2 instances."""
    conn = boto.ec2.connect_to_region(region)
    instances = conn.get_only_instances()
    return lookup(instances, filter_by=filter_by_kwargs)


def list_elb(region, filter_by_kwargs):
    """List all load balancers."""
    conn = boto.ec2.elb.connect_to_region(region)
    instances = conn.get_all_load_balancers()
    return lookup(instances, filter_by=filter_by_kwargs)


def list_rds(region, filter_by_kwargs):
    """List all RDS thingys."""
    conn = boto.rds.connect_to_region(region)
    instances = conn.get_all_dbinstances()
    return lookup(instances, filter_by=filter_by_kwargs)


def list_elasticache(region, filter_by_kwargs):
    """List all ElastiCache Clusters."""
    conn = boto.elasticache.connect_to_region(region)
    req = conn.describe_cache_clusters()
    data = req["DescribeCacheClustersResponse"]["DescribeCacheClustersResult"]["CacheClusters"]
    clusters = [x['CacheClusterId'] for x in data]
    return clusters


def list_autoscaling_group(region, filter_by_kwargs):
    """List all Auto Scaling Groups."""
    conn = boto.ec2.autoscale.connect_to_region(region)
    groups = conn.get_all_groups()
    return lookup(groups, filter_by=filter_by_kwargs)


def list_sqs(region, filter_by_kwargs):
    """List all SQS Queues."""
    conn = boto.sqs.connect_to_region(region)
    queues = conn.get_all_queues()
    return lookup(queues, filter_by=filter_by_kwargs)


def list_kinesis_applications(region, filter_by_kwargs):
    """List all the kinesis applications along with the shards for each stream"""
    conn = boto.kinesis.connect_to_region(region)
    streams = conn.list_streams()['StreamNames']
    kinesis_streams = {}
    for stream_name in streams:
        shard_ids = []
        shards = conn.describe_stream(stream_name)['StreamDescription']['Shards']
        for shard in shards:
            shard_ids.append(shard['ShardId'])
        kinesis_streams[stream_name] = shard_ids
    return kinesis_streams


def list_dynamodb(region, filter_by_kwargs):
    """List all DynamoDB tables."""
    conn = boto.dynamodb.connect_to_region(region)
    tables = conn.list_tables()
    return lookup(tables, filter_by=filter_by_kwargs)


list_resources = {
    'ec2': list_ec2,
    'elb': list_elb,
    'rds': list_rds,
    'elasticache': list_elasticache,
    'asg': list_autoscaling_group,
    'sqs': list_sqs,
    'kinesisapp': list_kinesis_applications,
    'dynamodb': list_dynamodb
}


def main():
    if '--version' in sys.argv:
        print(__version__)
        sys.exit()
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit()

    template, namespace, region, filters, __ = interpret_options(sys.argv[1:])

    # get the template first so this can fail before making a network request
    fs_path = os.path.abspath(os.path.dirname(template))
    loader = jinja2.FileSystemLoader(fs_path)
    jinja2_env = jinja2.Environment(loader=loader)
    template = jinja2_env.get_template(os.path.basename(template))

    # insure a valid region is set
    if region not in [r.name for r in boto.ec2.regions()]:
        raise ValueError("Invalid region:{0}".format(region))

    # should I be using ARNs?
    try:
        resources = list_resources[namespace](region, filters)
    except KeyError:
        print('ERROR: AWS namespace "{}" not supported or does not exist'
              .format(namespace))
        sys.exit(1)

    print(template.render({
        'filters': filters,
        'region': region,       # Use for Auth config section if needed
        'resources': resources,
    }))


if __name__ == '__main__':
    main()
