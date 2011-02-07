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
    """ Return a Track created from an mp4 file """
    from mutagen.mp4 import MP4

    mp4File = MP4(filename)

    length     = int(round(mp4File.info.length))
    bitrate    = int(mp4File.info.bitrate)
    samplerate = int(mp4File.info.sample_rate)

    try:    trackNumber = str(mp4File['trkn'][0][0])
    except: trackNumber = None

    try:    discNumber = str(mp4File['disk'][0][0])
    except: discNumber = None

    try:    date = str(mp4File['\xa9day'][0][0])
    except: date = None

    try:    title = str(mp4File['\xa9nam'][0])
    except: title = None

    try:    album = str(mp4File['\xa9alb'][0])
    except: album = None

    try:    artist = str(mp4File['\xa9ART'][0])
    except: artist = None

    try:    genre = str(mp4File['\xa9gen'][0])
    except: genre = None

    try:    albumArtist = str(mp4File['aART'][0])
    except: albumArtist = None

    return createFileTrack(filename, bitrate, length, samplerate, False, title, album, artist, albumArtist,
                None, genre, trackNumber, date, discNumber)
