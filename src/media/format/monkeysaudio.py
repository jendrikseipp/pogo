# -*- coding: utf-8 -*-
#
# Author: Ingelrest François (Francois.Ingelrest@gmail.com)
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

from mutagen.monkeysaudio  import MonkeysAudio
from media.track.fileTrack import FileTrack


def getTrack(file):
    """ Return a Track created from an APE file """
    track = FileTrack(file)
    mFile = MonkeysAudio(file)

    track.setBitrate(-1)
    track.setLength(int(round(mFile.info.length)))
    track.setSampleRate(int(mFile.info.sample_rate))

    try:    track.setNumber(int(mFile['Track'][0]))
    except: pass

    try:    track.setDate(int(mFile['Year'][0]))
    except: pass

    try:    track.setTitle(str(mFile['Title'][0]))
    except: pass

    try:    track.setAlbum(str(mFile['Album'][0]))
    except: pass

    try:    track.setArtist(str(mFile['Artist'][0]))
    except: pass

    try:    track.setGenre(str(mFile['Genre'][0]))
    except: pass

    return track
