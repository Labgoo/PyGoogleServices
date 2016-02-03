#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import re
import sys

from setuptools import setup, find_packages

root_dir = os.path.abspath(os.path.dirname(__file__))

def get_build_number():
    fname = 'build.info'
    if os.path.isfile(fname):
        with open(fname) as f:
            build_number = f.read()
            build_number = re.sub("[^a-z0-9]+","", build_number, flags=re.IGNORECASE)
            return '.' + build_number
            
    return ''

def get_version(package_name):
    build_number = get_build_number()
    
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    init_path = os.path.join(root_dir, *(package_components + ['__init__.py']))
    with codecs.open(init_path, 'r', 'utf-8') as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]+build_number

    return '0.1' + build_number


PACKAGE = 'googleservices'


setup(
    name='googleservices',
    version=get_version(PACKAGE),
    description="A lighweight python wrapper on top of google services REST API",
    author='Neta Krakover',
    author_email='krakover@gmail.com',
    maintainer='Neta Krakover',
    maintainer_email='krakover@gmail.com',
    url='https://github.com/Labgoo/PyGoogleServices',
    keywords=[],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    setup_requires=[
        'setuptools>=0.8',
        'setuptools-lint',
        'unittest2',
        'coverage',
        'nose'
    ],
    tests_require=[
        'mock',
    ],
    install_requires=[
        # 'jsonschema==2.3.0',
        'google-api-python-client==1.4.2',
        'oauth2client==1.3',
        # 'httplib2==0.9',
        'pycrypto==2.6.1',
        'Crypto',
        'requests==2.7.0',
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    test_suite='tests',
)
