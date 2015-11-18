#!/usr/bin/env python

__version__ = '1.0'

import urllib
import httplib
import getopt
import sys
from time import time
import random
from threading import Thread, currentThread
from math import pow, sqrt
import bisect
import re

###############

HOST = 'speedtest-po.vodafone.pt'
RUNS = 2
VERBOSE = 0
HTTPDEBUG = 0

###############

DOWNLOAD_FILES = [
    '/speedtest/random350x350.jpg',
    '/speedtest/random500x500.jpg',
    '/speedtest/random1500x1500.jpg',
]

UPLOAD_FILES = [
    132884,
    493638
]


def printv(msg):
    if VERBOSE:
        print msg


def downloadthread(connection, url):
    connection.request('GET', url, None, {'Connection': 'Keep-Alive'})
    response = connection.getresponse()
    self_thread = currentThread()
    self_thread.downloaded = len(response.read())


def download():
    total_downloaded = 0
    connections = []
    for run in range(RUNS):
        connection = httplib.HTTPConnection(HOST)
        connection.set_debuglevel(HTTPDEBUG)
        connection.connect()
        connections.append(connection)
    total_start_time = time()
    for current_file in DOWNLOAD_FILES:
        threads = []
        for run in range(RUNS):
            thread = Thread(target=downloadthread, args=(connections[run], current_file + '?x=' + str(int(time() * 1000))))
            thread.run_number = run
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
            total_downloaded += thread.downloaded
            printv('Run %d for %s finished' % (thread.run_number, current_file))
    total_ms = (time() - total_start_time) * 1000
    for connection in connections:
        connection.close()
    printv('Took %d ms to download %d bytes' % (total_ms, total_downloaded))
    return (total_downloaded * 8000 / total_ms)


def uploadthread(connection, data):
    url = '/speedtest/upload.php?x=' + str(random.random())
    connection.request('POST', url, data, {'Connection': 'Keep-Alive', 'Content-Type': 'application/x-www-form-urlencoded'})
    response = connection.getresponse()
    reply = response.read()
    self_thread = currentThread()
    self_thread.uploaded = int(reply.split('=')[1])


def upload():
    connections = []
    for run in range(RUNS):
        connection = httplib.HTTPConnection(HOST)
        connection.set_debuglevel(HTTPDEBUG)
        connection.connect()
        connections.append(connection)

    post_data = []
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for current_file_size in UPLOAD_FILES:
        values = {'content0': ''.join(random.choice(ALPHABET) for i in range(current_file_size))}
        post_data.append(urllib.urlencode(values))

    total_uploaded = 0
    total_start_time = time()
    for data in post_data:
        threads = []
        for run in range(RUNS):
            thread = Thread(target=uploadthread, args=(connections[run], data))
            thread.run_number = run
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
            printv('Run %d for %d bytes finished' % (thread.run_number, thread.uploaded))
            total_uploaded += thread.uploaded
    total_ms = (time() - total_start_time) * 1000
    for connection in connections:
        connection.close()
    printv('Took %d ms to upload %d bytes' % (total_ms, total_uploaded))
    return (total_uploaded * 8000 / total_ms)


def ping(server):
    connection = httplib.HTTPConnection(server)
    connection.set_debuglevel(HTTPDEBUG)
    connection.connect()
    times = []
    worst = 0
    for i in range(5):
        total_start_time = time()
        connection.request('GET', '/speedtest/latency.txt?x=' + str(random.random()), None, {'Connection': 'Keep-Alive'})
        response = connection.getresponse()
        response.read()
        total_ms = time() - total_start_time
        times.append(total_ms)
        if total_ms > worst:
            worst = total_ms
    times.remove(worst)
    total_ms = sum(times) * 250  # * 1000 / number of tries (4) = 250
    connection.close()
    printv('Latency for %s - %d' % (server, total_ms))
    return total_ms


def chooseserver():
    connection = httplib.HTTPConnection('www.speedtest.net')
    connection.set_debuglevel(HTTPDEBUG)
    connection.connect()
    now = int(time() * 1000)
    extra_headers = {
        'Connection': 'Keep-Alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
    }
    connection.request('GET', '/speedtest-config.php?x=' + str(now), None, extra_headers)
    response = connection.getresponse()
    reply = response.read()
    m = re.search('<client ip="([^"]*)" lat="([^"]*)" lon="([^"]*)"', reply)
    location = None
    if m is None:
        printv("Failed to retrieve coordinates")
        return None
    location = m.groups()
    printv('Your IP: %s\nYour latitude: %s\nYour longitude: %s' % location)
    connection.request('GET', '/speedtest-servers.php?x=' + str(now), None, extra_headers)
    response = connection.getresponse()
    reply = response.read()
    server_list = re.findall('<server url="([^"]*)" lat="([^"]*)" lon="([^"]*)"', reply)
    my_lat = float(location[1])
    my_lon = float(location[2])
    sorted_server_list = []
    for server in server_list:
        s_lat = float(server[1])
        s_lon = float(server[2])
        distance = sqrt(pow(s_lat - my_lat, 2) + pow(s_lon - my_lon, 2))
        bisect.insort_left(sorted_server_list, (distance, server[0]))
    best_server = (999999, '')
    for server in sorted_server_list[:10]:
        print server[1]
        m = re.search('http://([^/]+)/speedtest/upload\.php', server[1])
        if not m:
            continue
        server_host = m.groups()[0]
        latency = ping(server_host)
        if latency < best_server[0]:
            best_server = (latency, server_host)
    printv('Best server: ' + best_server[1])
    return best_server[1]


def usage():
    print '''
usage: pyspeedtest.py [-h] [-v] [-r N] [-m M] [-d L]

Test your bandwidth speed using Speedtest.net servers.

optional arguments:
 -h, --help         show this help message and exit
 -v                 enabled verbose mode
 -r N, --runs=N     use N runs (default is 2).
 -m M, --mode=M     test mode: 1 - download, 2 - upload, 4 - ping, 1 + 2 + 4 = 7 - all (default).
 -d L, --debug=L    set httpconnection debug level (default is 0).
 -s                 find best server
'''


def main():
    global VERBOSE, RUNS, HTTPDEBUG, HOST
    mode = 7
    findserver = False
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hr:vm:d:s",
            [
                "help",
                "runs=",
                "mode=",
                "debug=",
            ]
        )
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
            try:
                RUNS = int(a)
            except ValueError:
                print 'Bad runs value'
                sys.exit(2)
        elif o in ("-m", "--mode"):
            try:
                mode = int(a)
            except ValueError:
                print 'Bad mode value'
                sys.exit(2)
        elif o in ("-d", "--debug"):
            try:
                HTTPDEBUG = int(a)
            except ValueError:
                print 'Bad debug value'
                sys.exit(2)
        elif o == "-s":
            findserver = True

    if findserver:
        HOST = chooseserver()
    if mode & 4 == 4:
        print 'Ping: %d ms' % ping(HOST)
    if mode & 1 == 1:
        print 'Download speed: ' + pretty_speed(download())
    if mode & 2 == 2:
        print 'Upload speed: ' + pretty_speed(upload())


def pretty_speed(speed):
    units = ['bps', 'Kbps', 'Mbps', 'Gbps']
    unit = 0
    while speed >= 1024:
        speed /= 1024
        unit += 1
    return '%0.2f %s' % (speed, units[unit])

if __name__ == '__main__':
    main()
