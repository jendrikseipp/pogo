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
    """ Return a Track created from an mpc file """
    from mutagen.musepack      import Musepack
    from media.track.fileTrack import FileTrack

    track   = FileTrack(file)
    mpcFile = Musepack(file)

    track.setBitrate(int(mpcFile.info.bitrate * 1000))
    track.setLength(int(round(mpcFile.info.length)))
    track.setSampleRate(int(mpcFile.info.sample_rate))

    try:    track.setNumber(int(str(mpcFile['Track'])))
    except: pass

    try:    track.setDiscNumber(int(str(mpcFile['Discnumber'])))
    except: pass

    try:    track.setDate(int(str(mpcFile['Year'])))
    except: pass

    try:    track.setTitle(str(mpcFile['Title']))
    except: pass

    try:    track.setGenre(str(mpcFile['Genre']))
    except: pass

    try:    track.setMBTrackId(str(mpcFile['MUSICBRAINZ_TRACKID']))
    except: pass

    try:    track.setAlbum(str(mpcFile['Album']))
    except: pass

    try:    track.setArtist(str(mpcFile['Artist']))
    except: pass

    try:    track.setAlbumArtist(str(mpcFile['Album Artist']))
    except: pass

    return track
