# -*- coding: utf-8 -*-
#
# Copyright (c) 2007  François Ingelrest (Francois.Ingelrest@gmail.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

from pogo.media.format import createFileTrack


def getTrack(filename):
    """ Return a Track created from an mp3 file """
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3

    mp3File = MP3(filename)

    length = int(round(mp3File.info.length))
    bitrate = int(mp3File.info.bitrate)
    samplerate = int(mp3File.info.sample_rate)

    # Don't set VBR information for MP3 files (#1202195)
    isVBR = False

    try:
        id3 = ID3(filename)
    except:
        return createFileTrack(filename, bitrate, length, samplerate, isVBR)

    try:
        title = str(id3['TIT2'])
    except:
        title = None

    try:
        album = str(id3['TALB'])
    except:
        album = None

    try:
        artist = str(id3['TPE1'])
    except:
        artist = None

    try:
        albumArtist = str(id3['TPE2'])
    except:
        albumArtist = None

    try:
        musicbrainzId = id3['UFID:http://musicbrainz.org'].data
    except:
        musicbrainzId = None

    try:
        genre = str(id3['TCON'])
    except:
        genre = None

    try:
        trackNumber = str(id3['TRCK'])
    except:
        trackNumber = None

    try:
        date = str(id3['TDRC'][0].year)
    except:
        date = None

    try:
        discNumber = str(id3['TPOS'])
    except:
        discNumber = None

    return createFileTrack(filename, bitrate, length, samplerate, isVBR, title, album, artist, albumArtist,
                           musicbrainzId, genre, trackNumber, date, discNumber)
