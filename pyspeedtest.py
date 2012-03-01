#!/usr/bin/python

'''
TODO:
- upload test
- choose server based on latency (http://www.speedtest.net/speedtest-servers.php / http://SERVER/speedtest/latency.txt)
'''

import pycurl
from time import time

###############

HOST = 'http://speedtest.net.zon.pt'
CONNECTIONS = 2

###############

DOWNLOAD_FILES = [
	('/speedtest/random350x350.jpg',245388),
	('/speedtest/random500x500.jpg',505544),
	('/speedtest/random1500x1500.jpg',4468241),
]

m = None

def ignore_data_cb(buf):
	return len(buf)
	
def download():
	total_start_time = time() * 1000
	total_downloaded = 0
	for (current_file, current_file_size) in DOWNLOAD_FILES:
		num_processed = 0
		connection = 1
		total_downloaded += current_file_size * CONNECTIONS
		for c in m.handles:
			c.setopt(pycurl.URL, HOST + current_file + '?x=' + str(int(time()*1000)) + '&y=' + str(connection))
			c.setopt(pycurl.WRITEFUNCTION, ignore_data_cb)
			c.thread = connection
			c.filename = current_file
			m.add_handle(c)
			connection += 1
		while num_processed < CONNECTIONS:
			while 1:
			 	ret, num_handles = m.perform()
				if ret != pycurl.E_CALL_MULTI_PERFORM:
					break
			while 1:
				num_q, ok_list, err_list = m.info_read()
				for c in ok_list:
				 	m.remove_handle(c)
					print 'Thread %d finished %s' % (c.thread, c.filename)
				for c, errno, errmsg in err_list:
				 	m.remove_handle(c)
				 	print 'Fail WAT? final results might be unaccurate...'
				num_processed = num_processed + len(ok_list) + len(err_list)
				if num_q == 0:
				 	break
			m.select(1.0)
	total_ms = (time() * 1000) - total_start_time
	print 'Took %d ms to download %d bytes' % (total_ms, total_downloaded)
	print 'Download speed: %f bps' % (total_downloaded * 1000 * 8 / total_ms)
	
def main():
	download()
	
def init():
	global m
	m = pycurl.CurlMulti()
	m.handles = []
	for i in range(CONNECTIONS):
	 	c = pycurl.Curl()
	 	c.fp = None
	 	c.setopt(pycurl.FOLLOWLOCATION, 1)
	 	c.setopt(pycurl.MAXREDIRS, 5)
	 	c.setopt(pycurl.CONNECTTIMEOUT, 30)
	 	c.setopt(pycurl.TIMEOUT, 300)
	 	m.handles.append(c)

init()

if __name__ == '__main__':
	main()