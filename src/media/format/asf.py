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
    """ Return a Track created from an asf file """
    from mutagen.asf           import ASF
    from media.track.fileTrack import FileTrack

    track   = FileTrack(file)
    asfFile = ASF(file)

    track.setBitrate(int(asfFile.info.bitrate))
    track.setLength(int(round(asfFile.info.length)))
    track.setSampleRate(int(asfFile.info.sample_rate))

    try:    track.setNumber(int(asfFile['WM/TrackNumber'][0]))
    except: pass

    try:    track.setDiscNumber(int(asfFile['WM/PartOfSet'][0]))
    except: pass

    try:    track.setDate(int(asfFile['WM/Year'][0]))
    except: pass

    try:    track.setTitle(str(asfFile['Title'][0]))
    except: pass

    try:    track.setAlbum(str(asfFile['WM/AlbumTitle'][0]))
    except: pass

    try:    track.setArtist(str(asfFile['Author'][0]))
    except: pass

    try:    track.setAlbumArtist(str(asfFile['WM/AlbumArtist'][0]))
    except: pass

    try:    track.setGenre(str(asfFile['WM/Genre'][0]))
    except: pass

    try:    track.setMBTrackId(str(asfFile['MusicBrainz/Track Id'][0]))
    except: pass

    return track
