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
    """ Return a Track created from an APE file """
    from mutagen.monkeysaudio import MonkeysAudio

    mFile = MonkeysAudio(filename)

    length     = int(round(mFile.info.length))
    samplerate = int(mFile.info.sample_rate)

    try:    trackNumber = str(mFile['Track'][0])
    except: trackNumber = None

    try:    date = str(mFile['Year'][0])
    except: date = None

    try:    title = str(mFile['Title'][0])
    except: title = None

    try:    album = str(mFile['Album'][0])
    except: album = None

    try:    artist = str(mFile['Artist'][0])
    except: artist = None

    try:    genre = str(mFile['Genre'][0])
    except: genre = None

    return createFileTrack(filename, -1, length, samplerate, False, title, album, artist, None,
                None, genre, trackNumber, date, None)
