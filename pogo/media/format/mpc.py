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
    """ Return a Track created from an mpc file """
    from mutagen.musepack import Musepack

    mpcFile = Musepack(filename)

    length     = int(round(mpcFile.info.length))
    bitrate    = int(mpcFile.info.bitrate * 1000)
    samplerate = int(mpcFile.info.sample_rate)

    try:    trackNumber = str(mpcFile['Track'])
    except: trackNumber = None

    try:    discNumber = str(mpcFile['Discnumber'])
    except: discNumber = None

    try:    date = str(mpcFile['Year'])
    except: date = None

    try:    title = str(mpcFile['Title'])
    except: title = None

    try:    genre = str(mpcFile['Genre'])
    except: genre = None

    try:    musicbrainzId = str(mpcFile['MUSICBRAINZ_TRACKID'])
    except: musicbrainzId = None

    try:    album = str(mpcFile['Album'])
    except: album = None

    try:    artist = str(mpcFile['Artist'])
    except: artist = None

    try:    albumArtist = str(mpcFile['Album Artist'])
    except: albumArtist = None

    return createFileTrack(filename, bitrate, length, samplerate, False, title, album, artist, albumArtist,
                musicbrainzId, genre, trackNumber, date, discNumber)
