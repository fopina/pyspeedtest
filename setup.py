#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys

from setuptools import setup

from pyspeedtest import __program__, __version__


if sys.argv[-1] == 'pub':
    import pypandoc  # quick check
    os.system('python setup.py sdist upload')
    sys.exit()

if sys.argv[-1] == 'pubtest':
    import pypandoc  # quick check
    os.system('python setup.py sdist upload -r https://testpypi.python.org/pypi')
    sys.exit()

try:
    import pypandoc
    README = pypandoc.convert(os.path.join(os.path.dirname(__file__), 'README.md'), 'rst')
except (IOError, ImportError):
    README = open('README.md').read()

if sys.argv[-1] == 'readmerst':
    print(README)
    sys.exit()

# allow setup.py to be run from any path
os.chdir(os.path.dirname(os.path.abspath(__file__)))

setup(
    name=__program__,
    version=__version__,
    license='MIT',
    description='Speedtest.net Python script',
    long_description=README,
    url='https://github.com/fopina/pyspeedtest',
    download_url='https://github.com/fopina/pyspeedtest/tarball/v%s' %
    __version__,
    author='Filipe Pina',
    author_email='fopina@skmobi.com',
    py_modules=['pyspeedtest'],
    entry_points={
        'console_scripts': ['pyspeedtest=pyspeedtest:main']
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],
    keywords=['speedtest.net', 'speedtest', 'speed', 'test', 'bandwidth']
)
