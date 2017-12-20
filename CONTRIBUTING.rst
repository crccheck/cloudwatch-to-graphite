Contributing to Cloudwatch-to-Graphite
======================================

First off, thanks for taking the time to contribute!

These guidelines are a living document and open to change via a pull
request.

How Can I Contribute?
---------------------

Coding style
~~~~~~~~~~~~

It's a Python project, there is no reason not to follow
`PEP8 <https://www.python.org/dev/peps/pep-0008/>`__. There are a few exceptions:

* line length < 100 (not 80) if at all possible
* one-line docstrings are acceptable, but feel free to step up to full docstrings with parameters named and return values specified.

Open Issues
~~~~~~~~~~~

The project uses GitHub's built-in issue tracker. Check there if there
is something that matches your skills and interests.

Developing
~~~~~~~~~~

1. Optional: create a virtual environment:
   ``virtualenv cw2g && . cw2g/bin/activate``
2. Install requirements: ``pip install -r requirements.txt``
3. Run the test suite: ``make test``
4. Verify the tests pass over all supported Python versions: ``tox``

Pull requests
~~~~~~~~~~~~~

Standard-issue github project flow, summarized:

1. Fork the repo
2. Create a branch
3. Check in your changes
4. Create a pull request
5. An existing contributor will do a code review, and as applicable ask for
changes, mark the pull request with a :+1:, or merge it in, bump the
version number, and cut/tag a release.

Reporting Bugs
~~~~~~~~~~~~~~

This section guides you through submitting a bug report for cloudwatch-to-graphite.
Following these guidelines helps maintainers and the community
understand your report, reproduce the behavior, and find related
reports.

Before creating bug reports, please check the issue tracker, as you
might find out that you don't need to create one. When you are creating
a bug report, please include as many details as possible.

Code of Conduct
~~~~~~~~~~~~~~~

http://contributor-covenant.org/version/1/3/0/
