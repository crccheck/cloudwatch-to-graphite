# This is an example template file for getting metrics for a kinesis stream.
# If you want an example of a kinesis application look at kinesisapp.yml.js.
# Both can be run the same way
{%- set metrics = {'IncomingBytes': {'stat': 'Average', 'unit': 'Bytes'},
                   'IncomingRecords': {'stat': 'Average', 'unit': 'Count'},
                   'PutRecord.Bytes': {'stat': 'Average', 'unit': 'Bytes'},
                   'PutRecord.Latency': {'stat': 'Average', 'unit': 'Milliseconds'},
                   'PutRecord.Success': {'stat': 'Average', 'unit': 'Count'},
                   'GetRecords.Bytes': {'stat': 'Average', 'unit': 'Bytes'},
                   'GetRecords.IteratorAge': {'stat': 'Average', 'unit': 'Milliseconds'},
                   'GetRecords.IteratorAgeMilliseconds': {'stat': 'Average', 'unit': 'Milliseconds'},
                   'GetRecords.Latency': {'stat': 'Average', 'unit': 'Milliseconds'},
                   'GetRecords.Success': {'stat': 'Average', 'unit': 'Count'}
                   } -%}

# If connecting to a different region other than default, set region
Auth:
  region: "{{ region }}"
Metrics:
{%- for stream_name in resources %}
  {%- for metric in metrics %}
- Namespace: "AWS/Kinesis"
  MetricName: "{{ metric }}"
  Statistics: "{{ metrics[metric]['stat'] }}"
  Unit: "{{ metrics[metric]['unit'] }}"
  Dimensions:
    StreamName: "{{ stream_name }}"
  Options:
    Formatter: 'cloudwatch.%(Namespace)s.{{ stream_name}}.%(MetricName)s.%(statistic)s.%(Unit)s'
    Period: 5
  {% endfor %}
{% endfor %}
