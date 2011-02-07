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

import wave


def getTrack(filename):
    """ Return a Track created from an mp3 file """

    wavFile = wave.open(filename)

    length     = int(round(wavFile.getnframes() / float(wavFile.getframerate())))
    bitrate    = -1
    samplerate = wavFile.getframerate()

    wavFile.close()

    date          = None
    isVBR         = False
    title         = None
    album         = None
    genre         = None
    artist        = None
    discNumber    = None
    albumArtist   = None
    trackNumber   = None
    musicbrainzId = None

    return createFileTrack(filename, bitrate, length, samplerate, isVBR, title, album, artist, albumArtist,
                musicbrainzId, genre, trackNumber, date, discNumber)
