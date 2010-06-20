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

from media.format import createFileTrack


def getTrack(filename):
    """ Return a Track created from an Ogg Vorbis file """
    from mutagen.oggvorbis import OggVorbis

    oggFile = OggVorbis(filename)

    length     = int(round(oggFile.info.length))
    bitrate    = int(oggFile.info.bitrate)
    samplerate = int(oggFile.info.sample_rate)

    try:    title = str(oggFile['title'][0])
    except: title = None

    try:    album = str(oggFile['album'][0])
    except: album = None

    try:    artist = str(oggFile['artist'][0])
    except: artist = None

    try:    albumArtist = str(oggFile['albumartist'][0])
    except: albumArtist = None

    try:    genre = str(oggFile['genre'][0])
    except: genre = None

    try:    musicbrainzId = str(oggFile['musicbrainz_trackid'][0])
    except: musicbrainzId = None

    try:    trackNumber = str(oggFile['tracknumber'][0])
    except: trackNumber = None

    try:    discNumber = str(oggFile['discnumber'][0])
    except: discNumber = None

    try:    date = str(oggFile['date'][0])
    except: date = None

    return createFileTrack(filename, bitrate, length, samplerate, True, title, album, artist, albumArtist,
                musicbrainzId, genre, trackNumber, date, discNumber)
