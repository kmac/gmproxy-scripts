#!/usr/bin/env python2

#    This script fetches playlists using GMusicProxy (https://github.com/diraimondo/gmusicproxy)
#    Copyright (C) 2014  Kyle MacLeod  kyle.macleod is at gmail
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
A helper script for Google Play Music which retrieves .m3u playlists via GMusicProxy
(http://gmusicproxy.net/), optionally loading the playlist into
the current MPD playlist.

Usage
-----
Retrieve album playlist:
  {0} <options> --artist 'some artist' --title 'album title'

Retrieve album playlist and add into existing MPD playlist:
  {0} <options> --load --artist 'some artist' --title 'album title'

Retrieve playlist of entire collection:
  {0} <options> --collection

Retrieve all playlists:
  {0} <options> --playlists


<options>:
  -a|--artist: artist name
  -t|--title: album title
  -f|--force : force playlist overwriting
  -l|--load : load the playlist into currently mpd playlist using mpc
  -D : debug


Dependencies
------------
GMusicProxy needs to be installed
mpc (and mpd)
python-requests module


Configuration
-------------
You may need to define a ~/.gmproxyfetchrc file to override default values.

Contents of .gmproxyfetchrc:

[gmproxyfetch]

# the base url for the running gmusicproxy:
gmusicproxy-url = http://localhost:9999

# the playlist directory to store generated playlists:
mpd-playlist-dir = <base mpd path>/mpd/playlists

# the playlist prefix. All files will be prefixed with this (can be left blank):
playlist-prefix = gmusic-

'''

import ConfigParser
import getopt
import os
import os.path
import requests
import sys
import subprocess


# these are overwritten by contents of .gmproxyfetchrc, if defined
CONFIG = {
    # the base url for the running gmusicproxy:
    'gmusicproxy-url': 'http://localhost:9999',

    # the playlist directory to store generated playlists:
    'mpd-playlist-dir': os.path.join(os.getenv('HOME'), '.mpd', 'playlists'),

    # the playlist prefix. All files will be prefixed with this (can be left blank):
    'playlist-prefix': 'gmusic-',
}


# set to print extra debug info (see -D option):
DEBUG = False

class Usage(Exception):
    def __init__(self, msg='', include_doc=False):
        if msg is None:
            msg = ''
        self.msg = msg
        if include_doc:
            self.msg += '\n' + __doc__.format(os.path.basename(sys.argv[0]))


def info(s):
    print s

def debug(s):
    if DEBUG:
        print "DEBUG: " + s

def warn(s):
    print "WARN: " + s

def error(s):
    print "ERROR: " + s


def init_config():
    global CONFIG
    config_file = os.path.join(os.getenv('HOME'), '.gmproxyfetchrc')
    if os.path.exists(config_file):
        config = ConfigParser.SafeConfigParser(CONFIG)
        config.read(config_file)
        CONFIG['gmusicproxy-url'] = config.get('gmproxyfetch', 'gmusicproxy-url')
        CONFIG['mpd-playlist-dir'] = config.get('gmproxyfetch', 'mpd-playlist-dir')
        CONFIG['playlist-prefix'] = config.get('gmproxyfetch', 'playlist-prefix')
    debug("CONFIG: %s" % CONFIG)


def confirm_yes_default(prompt):
    confirm_val = raw_input('%s. Continue? (y/n) [y]: ' % prompt)
    return confirm_val.lower() in ('', "yes", "y", "true", "t", "1", "on")


def fetch_playlist(url, to_filename, args):
    """Fetches the URL into given to_filename.
    If 'load' is specified in args then the playlist is loaded via mpc.
    """
    r = requests.get(url)
    debug("r: %s" % r)
    if r.status_code != 200:
        warn('Request failed: %s' % str(r))
        return
    if len(r.text) <= 0:
        warn('Empty result: %s' % str(r))
        return
    if not args['force'] and os.path.exists(to_filename):
        if not confirm_yes_default('File exists: %s' % to_filename):
            info('File exists, aborted')
            return
    info('Writing playlist: ' + to_filename)
    with open(to_filename, 'w') as o:
        if args['load']:
            info(r.content)
        o.write(r.content)
    if args['load']:
        if not confirm_yes_default("Executing: mpc load '%s'" % to_filename):
            info('Aborted')
            return
        pl_name = os.path.basename(to_filename).split('.')[0]  # strip out the .m3u
        info('loading playlist: ' + pl_name)
        subprocess.check_call(['mpc', 'load', pl_name])


def get_album_playlist(args):
    """Retrieves an album playlist using 'artist' and 'title'.
    """
    if args['artist'] is None:
        raise Usage('ERROR: artist is required')
    if args['title'] is None:
        raise Usage('ERROR: album is required')
    #curl -s $CONFIG['gmusicproxy-url']/'get_by_search?type=album&artist=Alt-J&title=An%20Awesome%20Wave' > $HOME/.mpd/playlists/'Alt-J - An Awesome Wave.m3u'
    url = '%s/get_by_search?type=album&artist=%s&title=%s' % (CONFIG['gmusicproxy-url'], args['artist'], args['title'])
    to_filename = os.path.join(CONFIG['mpd-playlist-dir'], '%salbum-%s-%s.m3u' % (CONFIG['playlist-prefix'], args['artist'], args['title']))
    fetch_playlist(url, to_filename, args)


def get_collection_playlist(args):
    """Retrieves a playlist containing entire collection. Not currently used.
    """
    url = '%s/get_collection' % (CONFIG['gmusicproxy-url'])
    to_filename = os.path.join(CONFIG['mpd-playlist-dir'], '%scollection.m3u' % (CONFIG['playlist-prefix']))
    fetch_playlist(url, to_filename, args)


def get_all_playlists(args):
    """Retrieves all google playlists.
    """
    url = '%s/get_all_playlists' % (CONFIG['gmusicproxy-url'])
    all_playlists_filename = os.path.join(CONFIG['mpd-playlist-dir'], '%splaylists.m3u' % (CONFIG['playlist-prefix']))
    # don't use input args for the all playlists fetch - specifically, we don't want to load
    all_playlists_args = dict(args)
    all_playlists_args['load'] = False
    fetch_playlist(url, all_playlists_filename, all_playlists_args)
    with open(all_playlists_filename, 'r') as f:
        playlist_name = ''
        for line in f:
            line = line.strip()
            if line.startswith('#EXTINF'):
                playlist_name = line.split('#EXTINF:-1,')[-1]
            elif line.startswith('http:'):
                to_filename = os.path.join(CONFIG['mpd-playlist-dir'], '%splaylist-%s.m3u' % (CONFIG['playlist-prefix'], playlist_name))
                fetch_playlist(line, to_filename, args)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Process command line arguments
    processed_args = {
        'artist': None,
        'title': None,
        'force': False,
        'load': False,
    }

    # default operation is to search on artist/album
    operation_func = get_album_playlist

    try:
        try:
            opts, args = getopt.getopt(argv[1:],
                                       "a:t:hflD",
                                       ["artist=", "title=", "help", "force",
                                        "collection", "playlists", "load", "debug"])
        except getopt.error, msg:
            raise Usage(msg, False)
        for o, a in opts:
            if o in ("-h", "--help"):
                raise Usage(None, True)
            elif o in ("-a", "--artist"):
                processed_args['artist'] = a
                argv.remove(o)
                argv.remove(a)
            elif o in ("-f", "--force"):
                processed_args['force'] = True
                argv.remove(o)
            elif o in ("-t", "--title"):
                processed_args['title'] = a
                argv.remove(o)
                argv.remove(a)
            elif o in ("-l", "--load"):
                processed_args['load'] = True
                argv.remove(o)
            elif o in ("-D", "--debug"):
                global DEBUG
                DEBUG = True
                argv.remove(o)
            elif o in ("--playlists"):
                operation_func = get_all_playlists
                argv.remove(o)
            elif o in ("--collection"):
                operation_func = get_collection_playlist
                argv.remove(o)

        init_config()

        # invoke the operation
        operation_func(processed_args)

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "[for help use -h or --help]"
        return 2


if __name__ == "__main__":
    sys.exit(main())
