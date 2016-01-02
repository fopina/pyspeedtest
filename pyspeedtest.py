#!/usr/bin/env python

from __future__ import print_function

import bisect
import getopt
import logging
import os
import random
import re
import string
import sys

from math import sqrt
from threading import currentThread, Thread
from textwrap import dedent
from time import time

try:
    from httplib import HTTPConnection
except ImportError:
    from http.client import HTTPConnection

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

__program__ = 'pyspeedtest'
__script__ = os.path.basename(sys.argv[0])
__version__ = '1.2'


class SpeedTest(object):

    DOWNLOAD_FILES = [
        '/speedtest/random350x350.jpg',
        '/speedtest/random500x500.jpg',
        '/speedtest/random1500x1500.jpg'
    ]

    UPLOAD_FILES = [
        132884,
        493638
    ]

    def __init__(self, host=None, verbose=False, http_debug=0):
        self.host = host
        self.verbose = verbose
        self.http_debug = http_debug

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
                thread = Thread(
                    target=self.downloadthread,
                    args=(connections[run],
                          '%s?x=%d' % (current_file, int(time() * 1000))))
                thread.run_number = run + 1
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
                total_downloaded += thread.downloaded
                logging.info('Run %d for %s finished',
                             thread.run_number, current_file)
        total_ms = (time() - total_start_time) * 1000
        for connection in connections:
            connection.close()
        logging.info('Took %d ms to download %d bytes',
                     total_ms, total_downloaded)
        return total_downloaded * 8000 / total_ms

    def uploadthread(self, connection, data):
        url = '/speedtest/upload.php?x=%s' % random.random()
        connection.request('POST', url, data, {
            'Connection': 'Keep-Alive',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
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
        alphabet = string.digits + string.ascii_letters
        for current_file_size in SpeedTest.UPLOAD_FILES:
            values = {
                'content0': ''.join(
                    random.choice(alphabet) for i in range(current_file_size))
            }
            post_data.append(urlencode(values))

        total_uploaded = 0
        total_start_time = time()
        for data in post_data:
            threads = []
            for run in range(runs):
                thread = Thread(target=self.uploadthread,
                                args=(connections[run], data))
                thread.run_number = run + 1
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
                logging.info('Run %d for %d bytes finished',
                             thread.run_number, thread.uploaded)
                total_uploaded += thread.uploaded
        total_ms = (time() - total_start_time) * 1000
        for connection in connections:
            connection.close()
        logging.info('Took %d ms to upload %d bytes',
                     total_ms, total_uploaded)
        return total_uploaded * 8000 / total_ms

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
        for _ in range(5):
            total_start_time = time()
            connection.request(
                'GET',
                '/speedtest/latency.txt?x=%d' % random.random(),
                None,
                {'Connection': 'Keep-Alive'})
            response = connection.getresponse()
            response.read()
            total_ms = time() - total_start_time
            times.append(total_ms)
            if total_ms > worst:
                worst = total_ms
        times.remove(worst)
        total_ms = sum(times) * 250  # * 1000 / number of tries (4) = 250
        connection.close()
        logging.info('Latency for %s - %d', server, total_ms)
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
        connection.request(
            'GET', '/speedtest-config.php?x=%d' % now, None, extra_headers)
        response = connection.getresponse()
        reply = response.read().decode('utf-8')
        match = re.search(
            r'<client ip="([^"]*)" lat="([^"]*)" lon="([^"]*)"', reply)
        location = None
        if match is None:
            logging.info('Failed to retrieve coordinates')
            return None
        location = match.groups()
        logging.info('Your IP: %s\nYour latitude: %s\nYour longitude: %s' %
                     location)
        connection.request(
            'GET', '/speedtest-servers.php?x=%d' % now, None, extra_headers)
        response = connection.getresponse()
        reply = response.read().decode('utf-8')
        server_list = re.findall(
            r'<server url="([^"]*)" lat="([^"]*)" lon="([^"]*)"', reply)
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
            logging.info(server[1])
            match = re.search(
                r'http://([^/]+)/speedtest/upload\.php', server[1])
            if match is None:
                continue
            server_host = match.groups()[0]
            latency = self.ping(server_host)
            if latency < best_server[0]:
                best_server = (latency, server_host)
        print('Using server:', best_server[1])
        return best_server[1]


def error(*args):
    print(*args, file=sys.stderr)


def usage():
    return dedent('''\
        usage: %s [OPTION]...

        Test your bandwidth speed using Speedtest.net servers.

        optional arguments:

          -d L, --debug=L    set http connection debug level (default is 0)
          -m M, --mode=M     test mode: 1 - download
                                        2 - upload
                                        4 - ping
                                        1 + 2 + 4 = 7 - all (default)
          -r N, --runs=N     use N runs (default is 2)
          -s H, --server=H   use specific server
          -v,   --verbose    enabled verbose mode

          -h,   --help       show this help message and exit
                --version    output version information and exit
        ''' % __script__)


def version():
    return dedent('''\
        %s %s
        ''' % (__program__, __version__))


def parseargs():
    try:
        opts, _ = getopt.getopt(
            sys.argv[1:],
            'hvd:m:r:s:',
            [
                'help',
                'verbose',
                'version',
                'debug=',
                'mode=',
                'runs=',
                'server='
            ]
        )
    except getopt.GetoptError as err:
        error(err)
        error()
        error(usage())
        sys.exit(1)
    else:
        return opts


def main():
    opts = parseargs()
    speedtest = SpeedTest()

    mode = 7
    runs = 2

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(usage())
            sys.exit()
        elif opt == '--version':
            print(version())
            sys.exit()
        elif opt in ('-v', '--verbose'):
            speedtest.verbose = True
        elif opt in ('-r', '--runs'):
            try:
                runs = int(arg)
            except ValueError:
                error('Bad runs value')
                sys.exit(1)
        elif opt in ('-m', '--mode'):
            try:
                mode = int(arg)
            except ValueError:
                error('Bad mode value')
                sys.exit(1)
        elif opt in ('-d', '--debug'):
            try:
                speedtest.http_debug = int(arg)
            except ValueError:
                error('Bad debug value')
                sys.exit(1)
        elif opt == '-s':
            speedtest.host = arg

    logging.basicConfig(
        format='%(message)s',
        level=logging.INFO if speedtest.verbose else logging.ERROR)

    if mode & 4 == 4 and speedtest.host is not None:
        print('Ping: %d ms' % speedtest.ping())

    if mode & 1 == 1:
        print('Download speed: %s' % pretty_speed(speedtest.download(runs)))

    if mode & 2 == 2:
        print('Upload speed: %s' % pretty_speed(speedtest.upload(runs)))


def pretty_speed(speed):
    units = ['bps', 'Kbps', 'Mbps', 'Gbps']
    unit = 0
    while speed >= 1024:
        speed /= 1024
        unit += 1
    return '%0.2f %s' % (speed, units[unit])

if __name__ == '__main__':
    main()
