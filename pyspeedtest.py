#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import bisect
import logging
import os
import random
import re
import string
import sys

from math import sqrt
from threading import currentThread, Thread
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
__version__ = '1.2.1'
__description__ = 'Test your bandwidth speed using Speedtest.net servers.'


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

    ALPHABET = string.digits + string.ascii_letters

    def __init__(self, host=None, http_debug=0, runs=2, verbose=False):
        logging.basicConfig(
            format='%(message)s',
            level=logging.INFO if verbose else logging.ERROR)

        self._host = host
        self.http_debug = http_debug
        self.runs = runs

    @property
    def host(self):
        if not self._host:
            self._host = self.chooseserver()
        return self._host

    @host.setter
    def host(self, new_host):
        self._host = new_host

    def connect(self, url):
        try:
            connection = HTTPConnection(url)
            connection.set_debuglevel(self.http_debug)
            connection.connect()
            return connection
        except:
            error("Error connecting to '%s'" % url)

    def downloadthread(self, connection, url):
        connection.request('GET', url, None, {'Connection': 'Keep-Alive'})
        response = connection.getresponse()
        self_thread = currentThread()
        self_thread.downloaded = len(response.read())

    def download(self):
        total_downloaded = 0
        connections = []
        for run in range(self.runs):
            connections.append(self.connect(self.host))
        total_start_time = time()
        for current_file in SpeedTest.DOWNLOAD_FILES:
            threads = []
            for run in range(self.runs):
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

    def upload(self):
        connections = []
        for run in range(self.runs):
            connections.append(self.connect(self.host))

        post_data = []
        for current_file_size in SpeedTest.UPLOAD_FILES:
            values = {
                'content0': ''.join(
                    random.choice(SpeedTest.ALPHABET) for i in range(current_file_size))
            }
            post_data.append(urlencode(values))

        total_uploaded = 0
        total_start_time = time()
        for data in post_data:
            threads = []
            for run in range(self.runs):
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
        if not server:
            server = self.host

        connection = self.connect(server)
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
        connection = self.connect('www.speedtest.net')
        now = int(time() * 1000)
        extra_headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; '
                          'rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
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
        if not best_server[1]:
            error('Cannot find a test server')
        print('Using server: %s', best_server[1])
        return best_server[1]


def error(*args):
    print(*args, file=sys.stderr)
    sys.exit(1)


def parseargs(args):

    class SmartFormatter(argparse.HelpFormatter):

        def _split_lines(self, text, width):
            """argparse.RawTextHelpFormatter._split_lines"""
            if text.startswith('r|'):
                return text[2:].splitlines()
            return argparse.HelpFormatter._split_lines(self, text, width)

    def positive_int(value):
        try:
            ivalue = int(value)
            if ivalue < 0:
                raise ValueError
            return ivalue
        except ValueError:
            raise argparse.ArgumentTypeError(
                "invalid positive int value: '%s'" % value)

    parser = argparse.ArgumentParser(
        add_help=False,
        description=__description__,
        formatter_class=SmartFormatter,
        usage='%(prog)s [OPTION]...')
    parser.add_argument(
        '-d', '--debug',
        default=0,
        help='set http connection debug level (default is 0)',
        metavar='L',
        type=positive_int)
    parser.add_argument(
        '-h', '--help',
        action='help',
        help=argparse.SUPPRESS)
    parser.add_argument(
        '-m', '--mode',
        choices=range(1, 8),
        default=7,
        help='''r|test mode: 1 - download
           2 - upload
           4 - ping
           1 + 2 + 4 = 7 - all (default)''',
        metavar='M',
        type=int)
    parser.add_argument(
        '-r', '--runs',
        default=2,
        help='use N runs (default is 2)',
        metavar='N',
        type=positive_int)
    parser.add_argument(
        '-s', '--server',
        help='use specific server',
        metavar='H')
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='verbose',
        help='output additional information')
    parser.add_argument(
        '--version',
        action='version',
        version='{0} {1}'.format(__program__, __version__))

    return parser.parse_args(args)


def main(args=None):
    opts = parseargs(args)
    speedtest = SpeedTest(opts.server, opts.debug, opts.runs, opts.verbose)

    if opts.mode & 4 == 4 and opts.server is not None:
        print('Ping: %d ms' % speedtest.ping())

    if opts.mode & 1 == 1:
        print('Download speed: %s' % pretty_speed(speedtest.download()))

    if opts.mode & 2 == 2:
        print('Upload speed: %s' % pretty_speed(speedtest.upload()))


def pretty_speed(speed):
    units = ['bps', 'Kbps', 'Mbps', 'Gbps']
    unit = 0
    while speed >= 1024:
        speed /= 1024
        unit += 1
    return '%0.2f %s' % (speed, units[unit])

if __name__ == '__main__':
    main()
