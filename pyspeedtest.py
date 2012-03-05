#!/usr/bin/python

'''
TODO:
- improve upload() test to match speedtest.net flash app results (dns cache, keep-alive?)
- choose server based on latency (http://www.speedtest.net/speedtest-servers.php / http://SERVER/speedtest/latency.txt)
'''

import urllib, urllib2
import getopt, sys
from time import time
from random import random
from threading import Thread, currentThread

###############

HOST = 'http://speedtest-po.vodafone.pt'
RUNS = 2

###############

VERBOSE = 0

DOWNLOAD_FILES = [
	('/speedtest/random350x350.jpg',245388),
	('/speedtest/random500x500.jpg',505544),
	('/speedtest/random1500x1500.jpg',4468241),
]

UPLOAD_FILES = [
	132884,
	493638
]

def printv(msg):
	if VERBOSE : print msg
	
def download():
	total_start_time = time()
	total_downloaded = 0
	for (current_file, current_file_size) in DOWNLOAD_FILES:
		threads = []
		for run in range(RUNS):
			total_downloaded += current_file_size
			thread = Thread(target=urllib.urlretrieve, args = (HOST + current_file + '?x=' + str(int(time() * 1000)), '/dev/null'))
			thread.run_number = run
			thread.start()
			threads.append(thread)
		for thread in threads:
			thread.join()
			printv('Run %d for %s finished' % (thread.run_number, current_file))
	total_ms = (time() - total_start_time) * 1000
	printv('Took %d ms to download %d bytes' % (total_ms, total_downloaded))
	return (total_downloaded * 8000 / total_ms)

def uploadthread(req):
	response = urllib2.urlopen(req)
	reply = response.read()
	self_thread = currentThread()
	self_thread.uploaded = int(reply.split('=')[1])
	
def upload():
	url = HOST + '/speedtest/upload.php?x=' + str(random())
	total_start_time = time()
	total_uploaded = 0
	for current_file_size in UPLOAD_FILES:
		values = {'content0' : open('/dev/random').read(current_file_size) }
		data = urllib.urlencode(values)
		req = urllib2.Request(url, data)
		threads = []
		for run in range(RUNS):
			thread = Thread(target = uploadthread, kwargs = { 'req': req })
			thread.run_number = run
			thread.start()
			threads.append(thread)
		for thread in threads:
			thread.join()
			printv('Run %d for %d bytes finished' % (thread.run_number, thread.uploaded))
			total_uploaded += thread.uploaded
	total_ms = (time() - total_start_time) * 1000
	printv('Took %d ms to upload %d bytes' % (total_ms, total_uploaded))
	return (total_uploaded * 8000 / total_ms)

def usage():
	print '''
usage: pyspeedtest.py [-h] [-v] [-r N] [-m N]

Test your bandwidth speed using Speedtest.net servers.

optional arguments:
 -h, --help         show this help message and exit
 -v                 enabled verbose mode
 -r N, --runs=N     use N runs (default is 2).
 -m N, --mode=N     test mode: 1 - download only, 2 - upload only, 3 - both (default)
'''
		
def main():
	global VERBOSE, RUNS
	mode = 3
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hr:vm:", ["help", "runs=","mode="])
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
	for o, a in opts:
		if o == "-v":
			VERBOSE = 1
		elif o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o in ("-r", "--runs"):
			RUNS = a
		elif o in ("-m", "--mode"):
			try:
				mode = int(a)
			except ValueError:
				print 'Bad mode value'
				sys.exit(2)
	if mode & 1 == 1:
		print 'Download speed: ' + pretty_speed(download())
	if mode & 2 == 2:
		print 'Upload speed: ' + pretty_speed(upload())
	
def pretty_speed(speed):
	units = [ 'bps', 'Kbps', 'Mbps', 'Gbps' ]
	unit = 0
	while speed >= 1024:
		speed /= 1024
		unit += 1
	return '%0.2f %s' % (speed, units[unit])

if __name__ == '__main__':
	main()