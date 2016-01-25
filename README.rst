pyspeedtest
===========

Python script to test network bandwidth using Speedtest.net servers

Installation
------------

This fork of pyspeedtest adds support for Python 3 while still remaining compatible with Python 2.

::

    pip install --user git+https://github.com/brbsix/pyspeedtest

Usage
-----

::

    usage: pyspeedtest [OPTION]...

    Test your bandwidth speed using Speedtest.net servers.

    optional arguments:

      -d L, --debug=L    set http connection debug level (default is 0)
      -m M, --mode=M     test mode: 1 - download
                                    2 - upload
                                    4 - ping
                                    1 + 2 + 4 = 7 - all (default)
      -r N, --runs=N     use N runs (default is 2)
      -s H, --server=H   use specific server
      -v,   --verbose    output additional information

      -h,   --help       display this help and exit
            --version    output version information and exit
