"""
Usage:
  leadbutt [options]

Options:
  -h --help                   Show this screen.
  -c FILE --config-file=FILE  Path to a YAML configuration file [default: config.yaml].
"""
from calendar import timegm
import datetime
import sys

from docopt import docopt
import boto.ec2.cloudwatch
import yaml


region = 'us-east-1'  # TODO make this configurable


def output_results(results, metric):
    """
    Output the results to stdout.

    TODO: add AMPQ support for efficiency
    """
    formatter = ('cloudwatch.%(Namespace)s.%(dimension)s.%(MetricName)s'
        '.%(Statistics)s.%(Unit)s')
    context = dict(
        metric,
        dimension=metric['Dimensions'].values()[0],
    )
    for result in results:
        # get and then sanitize metric name
        metric_name = (formatter % context).replace('/', '.').lower()
        print metric_name,
        print result[metric['Statistics']],
        print timegm(result['Timestamp'].timetuple())


def get_config(fp):
    try:
        return yaml.load(fp)
    except yaml.YAMLError as e:
        sys.stderr.write(unicode(e))  # XXX python3
        sys.exit(1)  # TODO document exit codes


def main(config_file, **kwargs):
    if config_file == '-':
        config = get_config(sys.stdin)
    else:
        with open(config_file) as fp:
            config = get_config(fp)
    # print config

    # TODO use auth from config if exists
    conn = boto.ec2.cloudwatch.connect_to_region(region)
    for metric in config['metrics']:
        results = conn.get_metric_statistics(
            60,  # minimum: 60
            datetime.datetime.utcnow() - datetime.timedelta(seconds=60 * 5),
            datetime.datetime.utcnow(),
            metric['MetricName'],  # RequestCount
            metric['Namespace'],  # AWS/ELB
            metric['Statistics'],  # Sum
            dimensions=metric['Dimensions'],
            unit=metric['Unit'],
        )
        output_results(results, metric)


if __name__ == '__main__':
    options = docopt(__doc__)
    config_file = options.pop('--config-file')
    main(config_file=config_file, **options)
