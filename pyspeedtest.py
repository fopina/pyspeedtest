#!/usr/bin/python

'''
TODO:
- threaded downloading (like before with pycurl)
- upload test
- choose server based on latency (http://www.speedtest.net/speedtest-servers.php / http://SERVER/speedtest/latency.txt)
'''

import urllib
from time import time

###############

HOST = 'http://speedtest.net.zon.pt'
RUNS = 2

###############

DOWNLOAD_FILES = [
	('/speedtest/random350x350.jpg',245388),
	('/speedtest/random500x500.jpg',505544),
	('/speedtest/random1500x1500.jpg',4468241),
]

def download():
	total_start_time = time() * 1000
	total_downloaded = 0
	for (current_file, current_file_size) in DOWNLOAD_FILES:
		for run in range(RUNS):
			total_downloaded += current_file_size
			urllib.urlretrieve(HOST + current_file + '?x=' + str(int(time() * 1000)), '/dev/null')
			print 'Run %d for %s finished' % (run, current_file)
	total_ms = (time() * 1000) - total_start_time
	print 'Took %d ms to download %d bytes' % (total_ms, total_downloaded)
	print 'Download speed: ' + pretty_speed(total_downloaded * 8000 / total_ms)
	
def main():
	download()
	
def pretty_speed(speed):
	units = [ 'bps', 'Kbps', 'Mbps', 'Gbps' ]
	unit = 0
	while speed >= 1024:
		speed /= 1024
		unit += 1
	return str(speed) + ' ' + units[unit]

if __name__ == '__main__':
	main()