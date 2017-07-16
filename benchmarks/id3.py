#!/usr/bin/env python

import timeit

FILE = '/home/jendrik/You Cannot Cast Out The Demons (You Might As Well Dance).mp3'
NB_ITERS = 5000


def mutagen():
    # must do ampersand first
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3

    mp3File = MP3(FILE)

    length = int(round(mp3File.info.length))
    bitrate = int(mp3File.info.bitrate)

    id3 = ID3(FILE)

    title = str(id3['TIT2'])
    album = str(id3['TALB'])
    artist = str(id3['TPE1'])
    trackNumber = str(id3.get('TRCK'))


def hsaudiotag():
    from hsaudiotag import mpeg
    myfile = mpeg.Mpeg(FILE)
    tag = myfile.tag
    tag.artist
    tag.album
    tag.title
    tag.track
    myfile.duration


def hsaudiotag_auto():
    from hsaudiotag import auto
    myfile = auto.File(FILE)
    myfile.artist
    myfile.album
    myfile.title
    myfile.track
    myfile.duration


timers = ['mutagen', 'hsaudiotag', 'hsaudiotag_auto']

for name in timers:
    timer = timeit.Timer('%s()' % name, 'from __main__ import %s' % name)
    print '%15s:' % name, timer.timeit(NB_ITERS)
