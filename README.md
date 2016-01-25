pyspeedtest
==========

Python script to test network bandwidth using Speedtest.net servers

Installation
------------

This package is available from PyPI so you can easily install it with:

	pip install --user pyspeedtest

Usage
-----

	usage: pyspeedtest.py [-h] [-v] [-r N] [-m M] [-d L]

	Test your bandwidth speed using Speedtest.net servers.

	optional arguments:

		-d L, --debug=L    set http connection debug level (default is 0)
		-m M, --mode=M     test mode:	1 - download
																	2 - upload
																	4 - ping
																	1 + 2 + 4 = 7 - all (default)
		-r N, --runs=N     use N runs (default is 2)
		-s H, --server=H   use specific server
		-v,   --verbose    output additional information

		-h,   --help       display this help and exit
					--version    output version information and exit
