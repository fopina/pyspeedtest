#!/usr/bin/env python

from __future__ import print_function

import bisect
import getopt
import random
import re
import sys

from math import pow, sqrt
from threading import Thread, currentThread
from time import time

try:
    from httplib import HTTPConnection
except ImportError:
    from http.client import HTTPConnection

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

__version__ = '1.1'


class SpeedTest(object):
    DOWNLOAD_FILES = [
        '/speedtest/random350x350.jpg',
        '/speedtest/random500x500.jpg',
        '/speedtest/random1500x1500.jpg',
    ]

    UPLOAD_FILES = [
        132884,
        493638
    ]

    def __init__(self, host=None, verbose=False, http_debug=0):
        self.host = host
        self.verbose = verbose
        self.http_debug = http_debug

    def _printv(self, msg):
        if self.verbose:
            print(msg)

    def downloadthread(self, connection, url):
        connection.request('GET', url, None, {'Connection': 'Keep-Alive'})
        response = connection.getresponse()
        self_thread = currentThread()
        self_thread.downloaded = len(response.read())

    def download(self, runs=2):
        if self.host is None:
            self.host = self.chooseserver()

        total_downloaded = 0
        connections = []
        for run in range(runs):
            connection = HTTPConnection(self.host)
            connection.set_debuglevel(self.http_debug)
            connection.connect()
            connections.append(connection)
        total_start_time = time()
        for current_file in SpeedTest.DOWNLOAD_FILES:
            threads = []
            for run in range(runs):
                thread = Thread(target=self.downloadthread, args=(connections[run], current_file + '?x=' + str(int(time() * 1000))))
                thread.run_number = run
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
                total_downloaded += thread.downloaded
                self._printv('Run %d for %s finished' % (thread.run_number, current_file))
        total_ms = (time() - total_start_time) * 1000
        for connection in connections:
            connection.close()
        self._printv('Took %d ms to download %d bytes' % (total_ms, total_downloaded))
        return (total_downloaded * 8000 / total_ms)

    def uploadthread(self, connection, data):
        url = '/speedtest/upload.php?x=' + str(random.random())
        connection.request('POST', url, data, {'Connection': 'Keep-Alive', 'Content-Type': 'application/x-www-form-urlencoded'})
        response = connection.getresponse()
        reply = response.read().decode('utf-8')
        self_thread = currentThread()
        self_thread.uploaded = int(reply.split('=')[1])

    def upload(self, runs=2):
        if self.host is None:
            self.host = self.chooseserver()

        connections = []
        for run in range(runs):
            connection = HTTPConnection(self.host)
            connection.set_debuglevel(self.http_debug)
            connection.connect()
            connections.append(connection)

        post_data = []
        ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for current_file_size in SpeedTest.UPLOAD_FILES:
            values = {'content0': ''.join(random.choice(ALPHABET) for i in range(current_file_size))}
            post_data.append(urlencode(values))

        total_uploaded = 0
        total_start_time = time()
        for data in post_data:
            threads = []
            for run in range(runs):
                thread = Thread(target=self.uploadthread, args=(connections[run], data))
                thread.run_number = run
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
                self._printv('Run %d for %d bytes finished' % (thread.run_number, thread.uploaded))
                total_uploaded += thread.uploaded
        total_ms = (time() - total_start_time) * 1000
        for connection in connections:
            connection.close()
        self._printv('Took %d ms to upload %d bytes' % (total_ms, total_uploaded))
        return (total_uploaded * 8000 / total_ms)

    def ping(self, server=None):
        if server is None:
            server = self.host

        if server is None:
            raise Exception('No server specified')

        connection = HTTPConnection(server)
        connection.set_debuglevel(self.http_debug)
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
        self._printv('Latency for %s - %d' % (server, total_ms))
        return total_ms

    def chooseserver(self):
        connection = HTTPConnection('www.speedtest.net')
        connection.set_debuglevel(self.http_debug)
        connection.connect()
        now = int(time() * 1000)
        extra_headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
        }
        connection.request('GET', '/speedtest-config.php?x=' + str(now), None, extra_headers)
        response = connection.getresponse()
        reply = response.read().decode('utf-8')
        m = re.search(r'<client ip="([^"]*)" lat="([^"]*)" lon="([^"]*)"', reply)
        location = None
        if m is None:
            self._printv('Failed to retrieve coordinates')
            return None
        location = m.groups()
        self._printv('Your IP: %s\nYour latitude: %s\nYour longitude: %s' % location)
        connection.request('GET', '/speedtest-servers.php?x=' + str(now), None, extra_headers)
        response = connection.getresponse()
        reply = response.read().decode('utf-8')
        server_list = re.findall(r'<server url="([^"]*)" lat="([^"]*)" lon="([^"]*)"', reply)
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
            self._printv(server[1])
            m = re.search(r'http://([^/]+)/speedtest/upload\.php', server[1])
            if not m:
                continue
            server_host = m.groups()[0]
            latency = self.ping(server_host)
            if latency < best_server[0]:
                best_server = (latency, server_host)
        print('Using server: ' + best_server[1])
        return best_server[1]


def usage():
    print('''\
version: %s

usage: pyspeedtest.py [-h] [-v] [-r N] [-m M] [-d L]

Test your bandwidth speed using Speedtest.net servers.

optional arguments:
 -h, --help         show this help message and exit
 -v                 enabled verbose mode
 -r N, --runs=N     use N runs (default is 2).
 -m M, --mode=M     test mode: 1 - download, 2 - upload, 4 - ping, 1 + 2 + 4 = 7 - all (default).
 -d L, --debug=L    set httpconnection debug level (default is 0).
 -s H, --server=H   use specific server
''' % __version__)


def parseargs():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            'hr:vm:d:s:',
            [
                'help',
                'runs=',
                'mode=',
                'debug=',
                'server=',
            ]
        )
    except getopt.GetoptError as err:
        print(err)
        print()
        usage()
        sys.exit(1)
    else:
        return (opts, args)


def main():
    opts, args = parseargs()
    speedtest = SpeedTest()

    mode = 7
    runs = 2

    for o, a in opts:
        if o == '-v':
            speedtest.verbose = True
        elif o in ('-h', '--help'):
            usage()
            sys.exit()
        elif o in ('-r', '--runs'):
            try:
                runs = int(a)
            except ValueError:
                print('Bad runs value')
                sys.exit(1)
        elif o in ('-m', '--mode'):
            try:
                mode = int(a)
            except ValueError:
                print('Bad mode value')
                sys.exit(1)
        elif o in ('-d', '--debug'):
            try:
                speedtest.http_debug = int(a)
            except ValueError:
                print('Bad debug value')
                sys.exit(1)
        elif o == '-s':
            speedtest.host = a

    if mode & 4 == 4 and speedtest.host is not None:
        print('Ping: %d ms' % speedtest.ping())

    if mode & 1 == 1:
        print('Download speed: ' + pretty_speed(speedtest.download(runs)))

    if mode & 2 == 2:
        print('Upload speed: ' + pretty_speed(speedtest.upload(runs)))


def pretty_speed(speed):
    units = ['bps', 'Kbps', 'Mbps', 'Gbps']
    unit = 0
    while speed >= 1024:
        speed /= 1024
        unit += 1
    return '%0.2f %s' % (speed, units[unit])

if __name__ == '__main__':
    main()
