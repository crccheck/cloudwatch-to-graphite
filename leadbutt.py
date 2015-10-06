# -*- coding: UTF-8 -*-
"""
Usage:
  leadbutt [options]

Options:
  -h --help                   Show this screen.
  -c FILE --config-file=FILE  Path to a YAML configuration file [default: config.yaml].
  -p INT --period INT         Period length, in minutes (default: 1)
  -n INT                      Number of data points to try to get (default: 5)
  -v                          Verbose
  --version                   Show version.
"""
from __future__ import unicode_literals

from calendar import timegm
import datetime
import os.path
import sys

from docopt import docopt
import boto.ec2.cloudwatch
import yaml


# emulate six.text_type based on https://docs.python.org/3/howto/pyporting.html#str-unicode
if sys.version_info[0] >= 3:
    text_type = str
else:
    text_type = unicode

__version__ = '0.8.0'


# configuration

DEFAULT_REGION = 'us-east-1'

DEFAULT_OPTIONS = {
    'Period': 1,  # 1 minute
    'Count': 5,  # 5 periods
    'Formatter': ('cloudwatch.%(Namespace)s.%(dimension)s.%(MetricName)s'
        '.%(statistic)s.%(Unit)s')
}


def get_config(config_file):
    """Get configuration from a file."""
    def load(fp):
        try:
            return yaml.load(fp)
        except yaml.YAMLError as e:
            sys.stderr.write(text_type(e))
            sys.exit(1)  # TODO document exit codes

    if config_file == '-':
        return load(sys.stdin)
    if not os.path.exists(config_file):
        sys.stderr.write('ERROR: Must either run next to config.yaml or'
            ' specify a config file.\n' + __doc__)
        sys.exit(2)
    with open(config_file) as fp:
        return load(fp)


def get_options(config_options, local_options, cli_options):
    """
    Figure out what options to use based on the four places it can come from.

    Order of precedence:
    * cli_options      specified by the user at the command line
    * local_options    specified in the config file for the metric
    * config_options   specified in the config file at the base
    * DEFAULT_OPTIONS  hard coded defaults
    """
    options = DEFAULT_OPTIONS.copy()
    if config_options is not None:
        options.update(config_options)
    if local_options is not None:
        options.update(local_options)
    if cli_options is not None:
        options.update(cli_options)
    return options


def output_results(results, metric, options):
    """
    Output the results to stdout.

    TODO: add AMPQ support for efficiency
    """
    formatter = options['Formatter']
    context = metric.copy()  # XXX might need to sanitize this
    try:
        context['dimension'] = list(metric['Dimensions'].values())[0]
    except AttributeError:
        context['dimension'] = ''
    for result in results:
        stat_keys = metric['Statistics']
        if not isinstance(stat_keys, list):
            stat_keys = [stat_keys]
        for statistic in stat_keys:
            context['statistic'] = statistic
            # get and then sanitize metric name
            metric_name = (formatter % context).replace('/', '.').lower()
            line = '{} {} {}\n'.format(
                metric_name,
                result[statistic],
                timegm(result['Timestamp'].timetuple()),
            )
            sys.stdout.write(line)


def leadbutt(config_file, cli_options, verbose=False, **kwargs):
    config = get_config(config_file)
    config_options = config.get('Options')
    auth_options = config.get('Auth', {})

    region = auth_options.get('region', DEFAULT_REGION)
    connect_args = {
        'debug': 2 if verbose else 0,
    }
    if 'aws_access_key_id' in auth_options:
        connect_args['aws_access_key_id'] = auth_options['aws_access_key_id']
    if 'aws_secret_access_key' in auth_options:
        connect_args['aws_secret_access_key'] = auth_options['aws_secret_access_key']
    conn = boto.ec2.cloudwatch.connect_to_region(region, **connect_args)
    for metric in config['Metrics']:
        options = get_options(
            config_options, metric.get('Options'), cli_options)
        period_local = options['Period'] * 60
        count_local = options['Count']
        end_time = datetime.datetime.utcnow()
        start_time = end_time - datetime.timedelta(
            seconds=period_local * count_local)
        results = conn.get_metric_statistics(
            period_local,  # minimum: 60
            start_time,
            end_time,
            metric['MetricName'],  # RequestCount, CPUUtilization
            metric['Namespace'],  # AWS/ELB, AWS/EC2
            metric['Statistics'],  # Sum, Maximum
            dimensions=metric['Dimensions'],
            unit=metric['Unit'],  # Count, Percent
        )
        # sys.stderr.write('{} {}\n'.format(options['Count'], len(results)))
        output_results(results, metric, options)


def main(*args, **kwargs):
    options = docopt(__doc__, version=__version__)
    # help: http://boto.readthedocs.org/en/latest/ref/cloudwatch.html#boto.ec2.cloudwatch.CloudWatchConnection.get_metric_statistics
    config_file = options.pop('--config-file')
    period = options.pop('--period')
    count = options.pop('-n')
    verbose = options.pop('-v')
    cli_options = {}
    if period is not None:
        cli_options['Period'] = int(period)
    if count is not None:
        cli_options['Count'] = int(count)
    leadbutt(config_file, cli_options, verbose, **options)


if __name__ == '__main__':
    main()
