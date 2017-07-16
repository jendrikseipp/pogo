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
    """ Return a Track created from an asf file """
    from mutagen.asf import ASF

    asfFile = ASF(filename)

    length = int(round(asfFile.info.length))
    bitrate = int(asfFile.info.bitrate)
    samplerate = int(asfFile.info.sample_rate)

    try:
        trackNumber = str(asfFile['WM/TrackNumber'][0])
    except:
        trackNumber = None

    try:
        discNumber = str(asfFile['WM/PartOfSet'][0])
    except:
        discNumber = None

    try:
        date = str(asfFile['WM/Year'][0])
    except:
        date = None

    try:
        title = str(asfFile['Title'][0])
    except:
        title = None

    try:
        album = str(asfFile['WM/AlbumTitle'][0])
    except:
        album = None

    try:
        artist = str(asfFile['Author'][0])
    except:
        artist = None

    try:
        albumArtist = str(asfFile['WM/AlbumArtist'][0])
    except:
        albumArtist = None

    try:
        genre = str(asfFile['WM/Genre'][0])
    except:
        genre = None

    try:
        musicbrainzId = str(asfFile['MusicBrainz/Track Id'][0])
    except:
        musicbrainzId = None

    return createFileTrack(filename, bitrate, length, samplerate, False, title, album, artist, albumArtist,
                           musicbrainzId, genre, trackNumber, date, discNumber)
