from setuptools import setup


setup(
    name='cloudwatch-to-graphite',
    version='0.0.0',
    author='Chris Chang',
    author_email='c@crccheck.com',
    url='https://github.com/crccheck/cloudwatch-to-graphite',
    py_modules=['leadbutt'],
    entry_points={
        'console_scripts': [
            'leadbutt = leadbutt:main',
        ]
    },
    install_requires=[
        'boto',
        'PyYAML',
        'docopt',
    ],
    license='Apache License, Version 2.0',
    description='A Django app for adding object tools for models in the admin',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)
