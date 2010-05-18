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
    """ Return a Track created from an mp4 file """
    from mutagen.mp4           import MP4
    from media.track.fileTrack import FileTrack

    track   = FileTrack(file)
    mp4File = MP4(file)

    track.setBitrate(int(mp4File.info.bitrate))
    track.setLength(int(round(mp4File.info.length)))
    track.setSampleRate(int(mp4File.info.sample_rate))

    try:    track.setNumber(int(mp4File['trkn'][0][0]))
    except: pass

    try:    track.setDiscNumber(int(mp4File['disk'][0][0]))
    except: pass

    try:    track.setDate(int(mp4File['\xa9day'][0][0]))
    except: pass

    try:    track.setTitle(str(mp4File['\xa9nam'][0]))
    except: pass

    try:    track.setAlbum(str(mp4File['\xa9alb'][0]))
    except: pass

    try:    track.setArtist(str(mp4File['\xa9ART'][0]))
    except: pass

    try:    track.setGenre(str(mp4File['\xa9gen'][0]))
    except: pass

    try:    track.setAlbumArtist(str(mp4File['aART'][0]))
    except: pass

    # TODO How to retrieve the MusicBrainz track id? I don't have a sample file at hand.

    return track
