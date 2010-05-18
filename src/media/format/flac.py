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


def getTrack(file):
    """ Return a Track created from a FLAC file """
    from mutagen.flac          import FLAC
    from media.track.fileTrack import FileTrack

    track    = FileTrack(file)
    flacFile = FLAC(file)

    track.setBitrate(-1)
    track.setLength(int(round(flacFile.info.length)))
    track.setSampleRate(int(flacFile.info.sample_rate))

    try:    track.setTitle(str(flacFile['title'][0]))
    except: pass

    try:    track.setAlbum(str(flacFile['album'][0]))
    except: pass

    try:    track.setArtist(str(flacFile['artist'][0]))
    except: pass

    try:    track.setAlbumArtist(str(flacFile['albumartist'][0]))
    except: pass

    try:    track.setGenre(str(flacFile['genre'][0]))
    except: pass

    try:    track.setMBTrackId(str(flacFile['musicbrainz_trackid'][0]))
    except: pass

    try:    track.setNumber(int(str(flacFile['tracknumber'][0]).split('/')[0]))     # Track format may be 01/08, 02/08...
    except: pass

    try:    track.setDiscNumber(int(str(flacFile['discnumber'][0]).split('/')[0]))  # Disc number format may be 01/02, 02/02...
    except: pass

    try:    track.setDate(int(flacFile['date'][0]))
    except: pass

    return track
