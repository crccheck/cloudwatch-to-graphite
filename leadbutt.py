from calendar import timegm
import datetime
import sys

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


def main():
    # TODO add --config-file option, should also accept stdin
    with open('config.yaml') as fp:
        try:
            config = yaml.load(fp)
        except yaml.YAMLError as e:
            sys.stderr.write(unicode(e))  # XXX python3
            sys.exit(1)  # TODO document exit codes
    # print config
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
    main()
