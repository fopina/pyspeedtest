#!/usr/bin/python

'''
TODO:
- threaded up/downloading (like before with pycurl)
- choose server based on latency (http://www.speedtest.net/speedtest-servers.php / http://SERVER/speedtest/latency.txt)
'''

import urllib, urllib2
from time import time
from random import random

###############

HOST = 'http://speedtest-po.vodafone.pt'
RUNS = 4

###############

DOWNLOAD_FILES = [
	('/speedtest/random350x350.jpg',245388),
	('/speedtest/random500x500.jpg',505544),
	('/speedtest/random1500x1500.jpg',4468241),
]

UPLOAD_FILES = [
	132884,
	493638
]

def download():
	total_start_time = time()
	total_downloaded = 0
	for (current_file, current_file_size) in DOWNLOAD_FILES:
		for run in range(RUNS):
			total_downloaded += current_file_size
			urllib.urlretrieve(HOST + current_file + '?x=' + str(int(time() * 1000)), '/dev/null')
			print 'Run %d for %s finished' % (run, current_file)
	total_ms = (time() - total_start_time) * 1000
	print 'Took %d ms to download %d bytes' % (total_ms, total_downloaded)
	print 'Download speed: ' + pretty_speed(total_downloaded * 8000 / total_ms)

def create_data():
	return "asd"
	
def upload():
	url = HOST + '/speedtest/upload.php?x=' + str(random())
	total_start_time = time()
	total_uploaded = 0
	for current_file_size in UPLOAD_FILES:
		values = {'content0' : open('/dev/random').read(current_file_size) }
		data = urllib.urlencode(values)
		req = urllib2.Request(url, data)
		for run in range(RUNS):
			response = urllib2.urlopen(req)
			reply = response.read()
			total_uploaded += int(reply.split('=')[1])
			print 'Run %d for %d bytes finished' % (run, current_file_size)
	total_ms = (time() - total_start_time) * 1000
	print 'Took %d ms to upload %d bytes' % (total_ms, total_uploaded)
	print 'Upload speed: ' + pretty_speed(total_uploaded * 8000 / total_ms)
	
def main():
	download()
	upload()
	
def pretty_speed(speed):
	units = [ 'bps', 'Kbps', 'Mbps', 'Gbps' ]
	unit = 0
	while speed >= 1024:
		speed /= 1024
		unit += 1
	return '%0.2f %s' % (speed, units[unit])

if __name__ == '__main__':
	main()