gmproxy-scripts
===============

Helper scripts for working with GMusicProxy (http://gmusicproxy.net/)


gmproxy-fetch-playlist.py
-------------------------

This script is a front-end to fetching playlists through GMusicProxy.


From the help:

```
A helper script for Google Play Music which retrieves .m3u playlists via GMusicProxy
(http://gmusicproxy.net/), optionally loading the playlist into
the current MPD playlist.

Usage
-----
Retrieve album playlist:
  gmproxy-fetch-playlist.py <options> --artist 'some artist' --title 'album title'

Retrieve album playlist and add into existing MPD playlist:
  gmproxy-fetch-playlist.py <options> --load --artist 'some artist' --title 'album title'

Retrieve playlist of entire collection:
  gmproxy-fetch-playlist.py <options> --collection

Retrieve all playlists:
  gmproxy-fetch-playlist.py <options> --playlists


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

```
