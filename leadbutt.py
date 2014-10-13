# -*- coding: UTF-8 -*-
"""
Usage:
  leadbutt [options]

Options:
  -h --help                   Show this screen.
  -c FILE --config-file=FILE  Path to a YAML configuration file [default: config.yaml].
  -p INT --period INT         Period length, in minutes [default: 1]
  -n INT                      Number of data points to get [default: 5]
"""
from __future__ import unicode_literals

from calendar import timegm
import datetime
import sys

from docopt import docopt
import boto.ec2.cloudwatch
import yaml


# emulate six.text_type based on https://docs.python.org/3/howto/pyporting.html#str-unicode
if sys.version_info[0] >= 3:
    text_type = str
else:
    text_type = unicode


# configuration

DEFAULT_REGION = 'us-east-1'
DEFAULT_FORMAT = ('cloudwatch.%(Namespace)s.%(dimension)s.%(MetricName)s'
    '.%(Statistics)s.%(Unit)s')


def get_config(config_file):
    """Get configuration from a file."""
    def load(fp):
        try:
            return yaml.load(fp)
        except yaml.YAMLError as e:
            sys.stderr.write(text_type(e))  # XXX python3
            sys.exit(1)  # TODO document exit codes

    if config_file == '-':
        return load(sys.stdin)
    with open(config_file) as fp:
        return load(fp)


def output_results(results, metric):
    """
    Output the results to stdout.

    TODO: add AMPQ support for efficiency
    """
    options = metric.get('Options', {})
    formatter = options.get('Formatter', DEFAULT_FORMAT)
    context = metric.copy()
    try:
        context['dimension'] = list(metric['Dimensions'].values())[0]
    except AttributeError:
        context['dimension'] = ''
    for result in results:
        # get and then sanitize metric name
        metric_name = (formatter % context).replace('/', '.').lower()
        line = '{} {} {}\n'.format(
            metric_name,
            result[metric['Statistics']],
            timegm(result['Timestamp'].timetuple()),
        )
        sys.stdout.write(line)


def leadbutt(config_file, period, count, **kwargs):
    config = get_config(config_file)

    # TODO use auth from config if exists
    region = config.get('region', DEFAULT_REGION)
    conn = boto.ec2.cloudwatch.connect_to_region(region)
    for metric in config['metrics']:
        end_time = datetime.datetime.utcnow()
        start_time = end_time - datetime.timedelta(seconds=period * count)
        results = conn.get_metric_statistics(
            period,  # minimum: 60
            start_time,
            end_time,
            metric['MetricName'],  # RequestCount
            metric['Namespace'],  # AWS/ELB
            metric['Statistics'],  # Sum
            dimensions=metric['Dimensions'],
            unit=metric['Unit'],
        )
        output_results(results, metric)


def main(*args, **kwargs):
    options = docopt(__doc__)
    # help: http://boto.readthedocs.org/en/latest/ref/cloudwatch.html#boto.ec2.cloudwatch.CloudWatchConnection.get_metric_statistics
    config_file = options.pop('--config-file')
    period = int(options.pop('--period')) * 60
    count = int(options.pop('-n'))
    leadbutt(config_file, period, count, **options)


if __name__ == '__main__':
    main()
