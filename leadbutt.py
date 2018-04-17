# -*- coding: UTF-8 -*-
"""
Usage:
  leadbutt [options]

Options:
  -h --help                   Show this screen.
  -c FILE --config-file=FILE  Path to a YAML configuration file [default: config.yaml].
  -i INTERVAL                 Interval, in ms, to wait between metric requests. Doubles as the backoff multiplier. [default: 50]
  -m MAX_INTERVAL             The maximum interval time to back off to, in ms [default: 4000]
  -p INT --period INT         Period length, in minutes [default: 1]
  -n INT                      Number of data points to try to get [default: 5]
  -v                          Verbose
  --version                   Show version.
"""
from __future__ import unicode_literals

from calendar import timegm
import datetime
import os.path
import sys
import time

from docopt import docopt
import boto.ec2.cloudwatch
from retrying import retry
import yaml


# emulate six.text_type based on https://docs.python.org/3/howto/pyporting.html#str-unicode
if sys.version_info[0] >= 3:
    text_type = str
else:
    text_type = unicode

__version__ = '0.11.0'


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
            return yaml.safe_load(fp)
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
            # get and then sanitize metric name, first copy the unit name from the
            # result to the context to keep the default format happy
            context['Unit'] = result['Unit']
            metric_name = (formatter % context).replace('/', '.').lower()
            line = '{0} {1} {2}\n'.format(
                metric_name,
                result[statistic],
                timegm(result['Timestamp'].timetuple()),
            )
            sys.stdout.write(line)


def leadbutt(config_file, cli_options, verbose=False, **kwargs):

    # This function is defined in here so that the decorator can take CLI options, passed in from main()
    # we'll re-use the interval to sleep at the bottom of the loop that calls get_metric_statistics.
    @retry(wait_exponential_multiplier=kwargs.get('interval', None),
           wait_exponential_max=kwargs.get('max_interval', None),
           # give up at the point the next cron of this script probably runs; Period is minutes; some_max_delay needs ms
           stop_max_delay=cli_options['Count'] * cli_options['Period'] * 60 * 1000)
    def get_metric_statistics(**kwargs):
        """
        A thin wrapper around boto.cloudwatch.connection.get_metric_statistics, for the
        purpose of adding the @retry decorator
        :param kwargs:
        :return:
        """
        connection = kwargs.pop('connection')
        return connection.get_metric_statistics(**kwargs)

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
        # if 'Unit 'is in the config, request only that; else get all units
        unit = metric.get('Unit')
        metric_names = metric['MetricName']
        if not isinstance(metric_names, list):
            metric_names = [metric_names]
        for metric_name in metric_names:
            # we need a copy of the metric dict with the MetricName swapped out
            this_metric = metric.copy()
            this_metric['MetricName'] = metric_name
            results = get_metric_statistics(
                connection=conn,
                period=period_local,
                start_time=start_time,
                end_time=end_time,
                metric_name=metric_name,
                namespace=metric['Namespace'],
                statistics=metric['Statistics'],
                dimensions=metric['Dimensions'],
                unit=unit
            )
            output_results(results, this_metric, options)
            time.sleep(kwargs.get('interval', 0) / 1000.0)


def main(*args, **kwargs):
    options = docopt(__doc__, version=__version__)
    # help: http://boto.readthedocs.org/en/latest/ref/cloudwatch.html#boto.ec2.cloudwatch.CloudWatchConnection.get_metric_statistics
    config_file = options.pop('--config-file')
    period = int(options.pop('--period'))
    count = int(options.pop('-n'))
    verbose = options.pop('-v')
    cli_options = {}
    if period is not None:
        cli_options['Period'] = period
    if count is not None:
        cli_options['Count'] = count
    leadbutt(config_file, cli_options, verbose,
             interval=float(options.pop('-i')),
             max_interval=float(options.pop('-m'))
             )


if __name__ == '__main__':
    main()
