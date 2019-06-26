************
Discontinued
************

Back in early 2012 I found the need to test my VPS speed and speedtest.net seemed like a decent service (still is).
There was no CLI for it, so I made pyspeedtest. Since then a lot of other great options came up such as https://github.com/sivel/speedtest-cli or https://github.com/zpeters/speedtest which are better maintained (and even got higher visibility).

Now back to your original README content…

***********
pyspeedtest
***********

.. image:: https://travis-ci.org/fopina/pyspeedtest.svg?branch=master
    :target: https://travis-ci.org/fopina/pyspeedtest
    :alt: Build Status

.. image:: https://img.shields.io/pypi/v/pyspeedtest.svg
    :target: https://pypi.python.org/pypi/pyspeedtest
    :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/pyspeedtest.svg
    :target: https://pypi.python.org/pypi/pyspeedtest
    :alt: PyPI Python Versions

Python script to test network bandwidth using Speedtest.net servers

============
Installation
============


This package is available from PyPI so you can easily install it with:

.. code-block:: bash

    sudo pip install pyspeedtest

Or only for your user

.. code-block:: bash

    $ pip install --user pyspeedtest

=====
Usage
=====

In a terminal:

.. code-block:: bash

    $ pyspeedtest -h
    usage: pyspeedtest [OPTION]...

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

.. code-block:: bash

    $ pyspeedtest
    Using server: speedtest.serv.pt
    Ping: 9 ms
    Download speed: 148.17 Mbps
    Upload speed: 18.56 Mbps

From a python script:

.. code-block:: python

    >>> import pyspeedtest
    >>> st = pyspeedtest.SpeedTest()
    >>> st.ping()
    9.306252002716064
    >>> st.download()
    42762976.92544772
    >>> st.upload()
    19425388.307319913
