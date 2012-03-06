pyspeedtest
==========
Python script to test network bandwidth using Speedtest.net servers

Usage
-----

	usage: pyspeedtest.py [-h] [-v] [-r N] [-m M] [-d L]

	Test your bandwidth speed using Speedtest.net servers.

	optional arguments:
	 -h, --help         show this help message and exit
	 -v                 enabled verbose mode
	 -r N, --runs=N     use N runs (default is 2).
	 -m M, --mode=M     test mode: 1 - download, 2 - upload, 4 - ping, 1 + 2 + 4 = 7 - all (default).
	 -d L, --debug=L    set httpconnection debug level (default is 0).
	 -s                 find best server

