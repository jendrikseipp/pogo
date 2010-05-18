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
    """ Return a Track created from an mp3 file """
    from mutagen.mp3           import MP3
    from mutagen.id3           import ID3
    from media.track.fileTrack import FileTrack

    track   = FileTrack(file)
    mp3File = MP3(file)

    track.setBitrate(int(mp3File.info.bitrate))
    track.setLength(int(round(mp3File.info.length)))
    track.setSampleRate(int(mp3File.info.sample_rate))

    if mp3File.info.mode == 1:
        track.setVariableBitrate()

    try:
        id3 = ID3(file)
    except:
        return track

    try:    track.setTitle(str(id3['TIT2']))
    except: pass

    try:    track.setAlbum(str(id3['TALB']))
    except: pass

    try:    track.setArtist(str(id3['TPE1']))
    except: pass

    try:    track.setAlbumArtist(str(id3['TPE2']))
    except: pass

    try:    track.setMBTrackId(id3['UFID:http://musicbrainz.org'].data)
    except: pass

    try:    track.setGenre(str(id3['TCON']))
    except: pass

    try:    track.setNumber(int(str(id3['TRCK']).split('/')[0]))      # Track format may be 01/08, 02/08...
    except: pass

    try:    track.setDiscNumber(int(str(id3['TPOS']).split('/')[0]))  # Disc number format may be 01/08, 02/08...
    except: pass

    try:    track.setDate(int(id3['TDRC'][0].year))
    except: pass

    return track
