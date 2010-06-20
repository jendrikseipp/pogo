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


def createFileTrack(file, bitrate, length, samplerate, isVBR, title=None, album=None, artist=None, albumArtist=None,
                        musicbrainzId=None, genre=None, trackNumber=None, date=None, discNumber=None):
    """ Create a new FileTrack object based on the given information """
    from media.track.fileTrack import FileTrack

    track = FileTrack(file)

    track.setLength(length)
    track.setBitrate(bitrate)
    track.setSampleRate(samplerate)

    if isVBR:
        track.setVariableBitrate()

    if title is not None:
        track.setTitle(title)

    if album is not None:
        track.setAlbum(album)

    if artist is not None:
        track.setArtist(artist)

    if albumArtist is not None:
        track.setAlbumArtist(albumArtist)

    if musicbrainzId is not None:
        track.setMBTrackId(musicbrainzId)

    if genre is not None:
        track.setGenre(genre)

    if date is not None:
        try:    track.setDate(int(date))
        except: pass

    # The format of the track number may be 'X' or 'X/Y'
    # We discard Y since we don't use this information
    if trackNumber is not None:
        try:    track.setNumber(int(trackNumber.split('/')[0]))
        except: pass

    # The format of the disc number may be 'X' or 'X/Y'
    # We discard the disc number when Y is less than 2
    if discNumber is not None:
        try:
            discNumber = discNumber.split('/')

            if len(discNumber) == 1 or int(discNumber[1]) > 1:
                track.setDiscNumber(int(discNumber[0]))
        except:
            pass

    return track
