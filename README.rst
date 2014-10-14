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


Usage
-----

Cloudwatch-to-Graphite uses `boto`_, so make sure to follow its `configuration
instructions`_. The easiest way to do this is to set up the
``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY`` environment variables.

Set up a config.yaml. You can copy the included config.yaml.example. If your
graphite server is at graphite.local, you can send metrics like::

    leadbutt | nc -q0 graphite.local 2003

If you have several configs you want to switch between, you can specify a
custom configuration file and send extra data with::

    leadbutt --config-file=production.yaml -n 20 | nc -q0 graphite.local 2003

You can even generate configs on the fly and send it in like::

    generate_config_from_inventory | leadbutt --config-file=- | nc -q0 graphite.local 2003

.. _configuration instructions: http://boto.readthedocs.org/en/latest/boto_config_tut.html


config.yaml
-----------

What metrics to pull is in a YAML configuration file. See the example
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
