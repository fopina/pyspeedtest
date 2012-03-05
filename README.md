pyspeedtest
==========
Python script to test network bandwidth using Speedtest.net servers

Usage
-----

	pyspeedtest$ ./pyspeedtest.py -h

	usage: pyspeedtest.py [-h] [-v] [-r N] [-m M] [-d L]

	Test your bandwidth speed using Speedtest.net servers.

	optional arguments:
	 -h, --help         show this help message and exit
	 -v                 enabled verbose mode
	 -r N, --runs=N     use N runs (default is 2).
	 -m M, --mode=M     test mode: 1 - download only, 2 - upload only, 3 - both (default).
	 -d L, --debug=L    set httpconnection debug level (default is 0).

