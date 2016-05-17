#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import bisect
import itertools
import logging
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
__version__ = '1.2.6'
__description__ = 'Test your bandwidth speed using Speedtest.net servers.'

__supported_formats__ = ('default', 'json', 'xml')


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

    def __init__(self, host=None, http_debug=0, runs=2):
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
            raise Exception('Unable to connect to %r' % url)

    def downloadthread(self, connection, url):
        connection.request('GET', url, None, {'Connection': 'Keep-Alive'})
        response = connection.getresponse()
        self_thread = currentThread()
        self_thread.downloaded = len(response.read())

    def download(self):
        total_downloaded = 0
        connections = [
            self.connect(self.host) for i in range(self.runs)
        ]
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
                LOG.debug('Run %d for %s finished',
                          thread.run_number, current_file)
        total_ms = (time() - total_start_time) * 1000
        for connection in connections:
            connection.close()
        LOG.info('Took %d ms to download %d bytes',
                 total_ms, total_downloaded)
        return total_downloaded * 8000 / total_ms

    def uploadthread(self, connection, data):
        url = '/speedtest/upload.php?x=%d' % randint()
        connection.request('POST', url, data, {
            'Connection': 'Keep-Alive',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        response = connection.getresponse()
        reply = response.read().decode('utf-8')
        self_thread = currentThread()
        self_thread.uploaded = int(reply.split('=')[1])

    def upload(self):
        connections = [
            self.connect(self.host) for i in range(self.runs)
        ]

        post_data = [
            urlencode({'content0': content(s)}) for s in SpeedTest.UPLOAD_FILES
        ]

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
                LOG.debug('Run %d for %d bytes finished',
                          thread.run_number, thread.uploaded)
                total_uploaded += thread.uploaded
        total_ms = (time() - total_start_time) * 1000
        for connection in connections:
            connection.close()
        LOG.info('Took %d ms to upload %d bytes',
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
                '/speedtest/latency.txt?x=%d' % randint(),
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
        LOG.debug('Latency for %s - %d', server, total_ms)
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
            LOG.info('Failed to retrieve coordinates')
            return None
        location = match.groups()
        LOG.info('Your IP: %s', location[0])
        LOG.info('Your latitude: %s', location[1])
        LOG.info('Your longitude: %s', location[2])
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
            LOG.debug(server[1])
            match = re.search(
                r'http://([^/]+)/speedtest/upload\.php', server[1])
            if match is None:
                continue
            server_host = match.groups()[0]
            latency = self.ping(server_host)
            if latency < best_server[0]:
                best_server = (latency, server_host)
        if not best_server[1]:
            raise Exception('Cannot find a test server')
        LOG.debug('Best server: %s', best_server[1])
        return best_server[1]


def content(length):
    """Return alphanumeric string of indicated length."""
    cycle = itertools.cycle(SpeedTest.ALPHABET)
    return ''.join(next(cycle) for i in range(length))


def init_logging(loglevel=logging.WARNING):
    """Initialize program logger."""

    scriptlogger = logging.getLogger(__program__)

    # ensure logger is not reconfigured
    # it would be nice to use hasHandlers here, but that's Python 3 only
    if not scriptlogger.handlers:

        # set log level
        scriptlogger.setLevel(loglevel)

        # log message format
        fmt = '%(name)s:%(levelname)s: %(message)s'

        # configure terminal log
        streamhandler = logging.StreamHandler()
        streamhandler.setFormatter(logging.Formatter(fmt))
        scriptlogger.addHandler(streamhandler)


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
                'invalid positive int value: %r' % value)

    def format_enum(value):
        if value.lower() not in __supported_formats__:
            raise argparse.ArgumentTypeError(
                'output format not supported: %r' % value)
        return value

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
        '-f', '--format',
        default='default',
        help='output format ' + str(__supported_formats__),
        metavar='F',
        type=format_enum)
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='verbose',
        help='output additional information')
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ' + __version__)

    return parser.parse_args(args)


def perform_speedtest(opts):
    speedtest = SpeedTest(opts.server, opts.debug, opts.runs)

    if opts.format in __supported_formats__:

        if opts.format == 'default':

            print('Using server: %s' % speedtest.host)

            if opts.mode & 4 == 4:
                print('Ping: %d ms' % speedtest.ping())

            if opts.mode & 1 == 1:
                print('Download speed: %s' % pretty_speed(speedtest.download()))

            if opts.mode & 2 == 2:
                print('Upload speed: %s' % pretty_speed(speedtest.upload()))

        else:
            stats = dict(server=speedtest.host)
            if opts.mode & 4 == 4:
                stats['ping'] = speedtest.ping()
            if opts.mode & 1 == 1:
                stats['download'] = speedtest.download()
            if opts.mode & 2 == 2:
                stats['upload'] = speedtest.upload()
            if opts.format == 'json':
                from json import dumps
                print(dumps(stats))
            elif opts.format == 'xml':
                from xml.etree.ElementTree import Element, tostring
                xml = Element('data')
                for key, val in stats.items():
                    child = Element(key)
                    child.text = str(val)
                    xml.append(child)
                print(tostring(xml).decode('utf-8'))

    else:
        raise Exception('Output format not supported: %s' % opts.format)


def main(args=None):
    opts = parseargs(args)
    init_logging(logging.DEBUG if opts.verbose else logging.WARNING)
    try:
        perform_speedtest(opts)
    except Exception as e:
        if opts.verbose:
            LOG.exception(e)
        else:
            LOG.error(e)
        sys.exit(1)


def pretty_speed(speed):
    units = ['bps', 'Kbps', 'Mbps', 'Gbps']
    unit = 0
    while speed >= 1024:
        speed /= 1024
        unit += 1
    return '%0.2f %s' % (speed, units[unit])


def randint():
    """Return a random 12 digit integer."""
    return random.randint(100000000000, 999999999999)


LOG = logging.getLogger(__program__)

if __name__ == '__main__':
    main()
