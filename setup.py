#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import re
import sys

from setuptools import setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    init_path = os.path.join(root_dir, *(package_components + ['__init__.py']))
    with codecs.open(init_path, 'r', 'utf-8') as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.0'


if sys.version_info[0:2] < (2, 7):  # pragma: no cover
    test_loader = 'unittest2:TestLoader'
else:
    test_loader = 'unittest:TestLoader'


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
    packages=['googleservices'],
    # license='MIT',
    setup_requires=[
        'setuptools>=0.8',
    ],
    tests_require=[
        #'mock',
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
    test_loader=test_loader,
)