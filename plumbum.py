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

import argparse
import sys

import boto
import boto.dynamodb
import boto.ec2
import boto.emr
import boto.ec2.elb
import boto.ec2.cloudwatch
import boto.rds
import boto.elasticache
import boto.ec2.autoscale
import boto.kinesis
import boto.sqs
import jinja2
import os.path

from leadbutt import __version__

# DEFAULT_NAMESPACE = 'ec2'  # TODO
DEFAULT_REGION = 'us-east-1'


class CliArgsException(Exception):
    pass


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


def interpret_options(args=sys.argv[1:]):

    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument("-r", "--region", help="AWS region", default=DEFAULT_REGION)
    parser.add_argument("-f", "--filter", action='append', default=[],
                        help="filter to apply to AWS objects in key=value form, can be used multiple times")
    parser.add_argument('--token', action='append', help='a key=value pair to use when populating templates')
    parser.add_argument("template", type=str, help="the template to interpret")
    parser.add_argument("namespace", type=str, help="AWS namespace")

    args = parser.parse_args(args=args)

    # filters are passed in as list of key=values pairs, we need a dictionary to pass to lookup()
    filters = dict([x.split('=', 1) for x in args.filter])

    # Support 'ec2' (human friendly) and 'AWS/EC2' (how CloudWatch natively calls these things)
    if args.namespace is not None:  # Just making test pass, argparse will catch this missing.
        namespace = args.namespace.rsplit('/', 2)[-1].lower()
    else:
        namespace = None
    return args.template, namespace, args.region, filters, args.token


def list_billing(region, filter_by_kwargs):
    """List available billing metrics"""
    conn = boto.ec2.cloudwatch.connect_to_region(region)
    metrics = conn.list_metrics(metric_name='EstimatedCharges')
    # Filtering is based on metric Dimensions.  Only really valuable one is
    # ServiceName.
    if filter_by_kwargs:
        filter_key = filter_by_kwargs.keys()[0]
        filter_value = filter_by_kwargs.values()[0]
        if filter_value:
            filtered_metrics = [x for x in metrics if x.dimensions.get(filter_key) and x.dimensions.get(filter_key)[0] == filter_value]
        else:
            # ServiceName=''
            filtered_metrics = [x for x in metrics if not x.dimensions.get(filter_key)]
    else:
        filtered_metrics = metrics
    return filtered_metrics


def list_cloudfront(region, filter_by_kwargs):
    """List running ec2 instances."""
    conn = boto.connect_cloudfront()
    instances = conn.get_all_distributions()
    return lookup(instances, filter_by=filter_by_kwargs)


def list_ec2(region, filter_by_kwargs):
    """List running ec2 instances."""
    conn = boto.ec2.connect_to_region(region)
    instances = conn.get_only_instances()
    return lookup(instances, filter_by=filter_by_kwargs)

def list_ebs(region, filter_by_kwargs):
    """List running ebs volumes."""
    conn = boto.ec2.connect_to_region(region)
    instances = conn.get_all_volumes()
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
    if filter_by_kwargs:
        clusters = [x['CacheClusterId'] for x in data if x[filter_by_kwargs.keys()[0]] == filter_by_kwargs.values()[0]]
    else:
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


def list_emr(region, filter_by_kwargs):
    conn = boto.emr.connect_to_region(region)
    q_list = conn.list_clusters(cluster_states=['WAITING', 'RUNNING'])
    queues = q_list.clusters
    return lookup(queues, filter_by=filter_by_kwargs)

list_resources = {
    'cloudfront': list_cloudfront,
    'ec2': list_ec2,
    'ebs': list_ebs,
    'elb': list_elb,
    'rds': list_rds,
    'elasticache': list_elasticache,
    'asg': list_autoscaling_group,
    'sqs': list_sqs,
    'kinesisapp': list_kinesis_applications,
    'dynamodb': list_dynamodb,
    'billing': list_billing,
    'emr': list_emr,
}


def main():

    template, namespace, region, filters, tokens = interpret_options()

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

    # base tokens
    template_tokens = {
        'filters': filters,
        'region': region,  # Use for Auth config section if needed
        'resources': resources,
    }
    # add tokens passed as cli args:
    if tokens is not None:
        for token_pair in tokens:
            if token_pair.count('=') != 1:
                raise CliArgsException("token pair '{0}' invalid, must contain exactly one '=' character.".format(token_pair))
            (key, value) = token_pair.split('=')
            template_tokens[key] = value

    print(template.render(template_tokens))


if __name__ == '__main__':
    main()
