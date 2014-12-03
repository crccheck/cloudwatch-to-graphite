Here are some sample jinja2 templates you can use with `plumbum` to generate
configuration files for `leadbutt`.


Usage
-----

### Create a config file for getting metrics from ec2:

    plumbum sample_templates/ec2.yml.j2 ec2 > ec2.yml

### Using that config file

    leadbutt -c ec2.yml | nc -q0 graphite.local 2003


For more, see `plumbum --help`
