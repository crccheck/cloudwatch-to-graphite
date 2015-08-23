{%- set metrics = {'DataBytesProcessed': {'stat': 'Average', 'unit': 'Bytes'},
                   'KinesisDataFetcher.getRecords.Success': {'stat': 'Average', 'unit': 'Count'},
                   'KinesisDataFetcher.getRecords.Time': {'stat': 'Average', 'unit': 'Milliseconds'},
                   'MillisBehindLatest': {'stat': 'Average', 'unit': 'Milliseconds'},
                   'RecordsProcessed': {'stat': 'Average', 'unit': 'Count'},
                   'Success': {'stat': 'Average', 'unit': 'Count'},
                   'Time': {'stat': 'Average', 'unit': 'Milliseconds'},
                   'UpdateLease.Success': {'stat': 'Average', 'unit': 'Count'},
                   'UpdateLease.Time': {'stat': 'Average', 'unit': 'Milliseconds'}
                   } -%}

# If connecting to a different region other than default, set region
Auth:
  region: "{{ region }}"
Metrics:
{%- for stream_name, shards in resources.iteritems() %}
  {%- for shard in shards %}
    {%- for metric in metrics %}
- Namespace: "kinesis-application-name"
  MetricName: "{{ metric }}"
  Statistics: "{{ metrics[metric]['stat'] }}"
  Unit: "{{ metrics[metric]['unit'] }}"
  Dimensions:
    ShardId: "{{ shard }}"
    Operation: "ProcessTask"
  Options:
    Formatter: 'cloudwatch.{{ stream_name}}.%(Namespace)s.%(MetricName)s.{{ shard }}.%(statistic)s.%(Unit)s'
    Period: 5
     {% endfor %}
   {% endfor %}
{% endfor %}
