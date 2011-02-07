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

from media.format import createFileTrack


def getTrack(filename):
    """ Return a Track created from a FLAC file """
    from mutagen.flac import FLAC

    flacFile = FLAC(filename)

    length     = int(round(flacFile.info.length))
    samplerate = int(flacFile.info.sample_rate)

    try:    title = str(flacFile['title'][0])
    except: title = None

    try:    album = str(flacFile['album'][0])
    except: album = None

    try:    artist = str(flacFile['artist'][0])
    except: artist = None

    try:    albumArtist = str(flacFile['albumartist'][0])
    except: albumArtist = None

    try:    genre = str(flacFile['genre'][0])
    except: genre = None

    try:    musicbrainzId = str(flacFile['musicbrainz_trackid'][0])
    except: musicbrainzId = None

    try:    trackNumber = str(flacFile['tracknumber'][0])
    except: trackNumber = None

    try:    discNumber = str(flacFile['discnumber'][0])
    except: discNumber = None

    try:    date = str(flacFile['date'][0])
    except: date = None

    return createFileTrack(filename, -1, length, samplerate, False, title, album, artist, albumArtist,
                musicbrainzId, genre, trackNumber, date, discNumber)
