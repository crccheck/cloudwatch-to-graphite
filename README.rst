Cloudwatch-to-Graphite
======================

.. image:: https://travis-ci.org/crccheck/cloudwatch-to-graphite.svg
    :target: https://travis-ci.org/crccheck/cloudwatch-to-graphite

Cloudwatch-to-Graphite (leadbutt) is a small utility to take metrics from
CloudWatch to Graphite.


Installation
------------

Install using pip::

    pip install cloudwatch-to-graphite

Configuring ``boto``
~~~~~~~~~~~~~~~~~~~~

Cloudwatch-to-Graphite uses `boto`_, so make sure to follow its `configuration
instructions`_. The easiest way to do this is to set up the
``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY`` environment variables.

.. _configuration instructions: http://boto.readthedocs.org/en/latest/boto_config_tut.html


Usage
-----

Configuration Files
~~~~~~~~~~~~~~~~~~~

If you have a simple setup, the easiest way to get started is to set up a
config.yaml. You can copy the included config.yaml.example. Then just run::

    leadbutt

If you have several configs you want to switch between, you can specify a
custom configuration file::

    leadbutt --config-file=production.yaml -n 20

You can even generate configs on the fly and send them in via stdin by setting
the config file to '-'::

    generate_config_from_inventory | leadbutt --config-file=-

There's a helper to generate configuration files called ``plumbum``.  Use it like::

    plumbum [-r REGION] [-f FILTER] [--token TOKEN] namespace template

Namespace is the CloudWatch namespace for the resources of interest; for example ``AWS/RDS``.
The template is a Jinja2 template. You can add arbitrary replacement tokens, eg ``{{ replace_me }}``, and then
pass in values on the CLI via ``--token``. For example, if you called::

    plumbum --token replace_me='hello, world' AWS/RDS sample_templates/rds.yml.j2

You would get all instances of ``{{ replace_me }}`` in the templace replaced with ``hello, world``.


Sending Data to Graphite
~~~~~~~~~~~~~~~~~~~~~~~~

If your graphite server is at graphite.local, you can send metrics by chaining
with netcat::

    leadbutt | nc -q0 graphite.local 2003

Or if you want to use UDP::

    leadbutt | nc -uw0 graphite.local 2003

If you need to namespace your metrics for a hosted Graphite provider, you could
provide a custom formatter, but the easiest way is to just run the output
through awk::

    leadbutt | \
      awk -v namespace="$HOSTEDGRAPHITE_APIKEY" '{print namespace"."$0}' | \
      nc -uw0 my-graphite-provider.xxx 2003

Customizing Your Graphite Metric Names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set the ``Formatter`` option to set the template used to generate Graphite
metric names. I wasn't sure what should be default, so I copied
`cloudwatch2graphite`_'s. Here's what it looks like::

    cloudwatch.%(Namespace)s.%(dimension)s.%(MetricName)s.%(statistic)s.%(Unit)s

TitleCased variables come directly from the YAML configuration, while lowercase
variables are derived:

* **statistic** -- the current statistic since ``Statistics`` can be a list
* **dimension** -- the dimension value, e.g. "i-r0b0t" or "my-load-balancer"

The format string is Python's `%-style <https://docs.python.org/2/library/stdtypes.html#string-formatting>`_.

config.yaml
-----------

What metrics are pulled is in a YAML configuration file. See the example
config.yaml.example for an idea of what you can do.


Developing
----------

Install requirements::

    pip install -r requirements.txt

Running test suite::

    make test

Verifying tests run over all supported Python versions::

    tox


Useful References
-----------------

* `CloudWatch Reference <http://docs.aws.amazon.com/AmazonCloudWatch/latest/DeveloperGuide/CW_Support_For_AWS.html>`_
* `boto CloudWatch docs <http://boto.readthedocs.org/en/latest/ref/cloudwatch.html>`_


Prior Art
---------

Cloudwatch-to-Graphite was inspired by edasque's `cloudwatch2graphite`_. I was
looking to expand it, but I wanted to use `boto`_.

.. _cloudwatch2graphite: https://github.com/edasque/cloudwatch2graphite
.. _boto: https://boto.readthedocs.org/en/latest/
