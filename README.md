pyspeedtest
==========

[![Build Status](https://travis-ci.org/fopina/pyspeedtest.svg?branch=master)](https://travis-ci.org/fopina/pyspeedtest) [![PyPI Version](https://img.shields.io/pypi/v/pyspeedtest.svg)](https://pypi.python.org/pypi/pyspeedtest) [![PyPI Python Versions](https://img.shields.io/pypi/pyversions/pyspeedtest.svg)](https://pypi.python.org/pypi/pyspeedtest)

Python script to test network bandwidth using Speedtest.net servers

Installation
------------

This package is available from PyPI so you can easily install it with:

	pip install --user pyspeedtest

Usage
-----

```
usage: pyspeedtest.py [OPTION]...

Test your bandwidth speed using Speedtest.net servers.

optional arguments:
  -d L, --debug L   set http connection debug level (default is 0)
  -m M, --mode M    test mode: 1 - download
                               2 - upload
                               4 - ping
                               1 + 2 + 4 = 7 - all (default)
  -r N, --runs N    use N runs (default is 2)
  -s H, --server H  use specific server
  -v, --verbose     output additional information
  --version         show program's version number and exit
```
