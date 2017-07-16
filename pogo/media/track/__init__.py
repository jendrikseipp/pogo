# -*- coding: utf-8 -*-
#
# Copyright (c) 2007  François Ingelrest (Francois.Ingelrest@gmail.com)
# Copyright (c) 2010  Jendrik Seipp (jendrikseipp@web.de)
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

import os.path
from gettext import gettext as _

from pogo import tools
from pogo.tools import consts, sec2str


# Tags asscociated to a track
# The order should not be changed for compatibility reasons
(
    TAG_RES,  # Full path to the resource
    TAG_SCH,  # URI scheme (e.g., file)
    TAG_NUM,  # Track number
    TAG_TIT,  # Title
    TAG_ART,  # Artist
    TAG_ALB,  # Album
    TAG_LEN,  # Length in seconds
    TAG_AAR,  # Album artist
    TAG_DNB,  # Disc number
    TAG_GEN,  # Genre
    TAG_DAT,  # Year
    TAG_MBT,  # MusicBrainz track id
    TAG_BTR,  # Bit rate
    TAG_MOD,  # Constant or variable bit rate
    TAG_SMP,  # Sample rate
) = list(range(15))


# Special fields that may be used to call format()
FIELDS = (
            ( 'track'       , _('Track number')                          ),
            ( 'title'       , _('Title')                                 ),
            ( 'artist'      , _('Artist')                                ),
            ( 'album'       , _('Album')                                 ),
            ( 'genre'       , _('Genre')                                 ),
            ( 'date'        , _('Date')                                  ),
            ( 'disc'        , _('Disc number')                           ),
            ( 'bitrate'     , _('Bit rate')                              ),
            ( 'sample_rate' , _('Sample rate')                           ),
            ( 'duration_sec', _('Duration in seconds (e.g., 194)')       ),
            ( 'duration_str', _('Duration as a string (e.g., 3:14)')     ),
            ( 'path'        , _('Full path to the file')                 ),
         )


def getFormatSpecialFields(usePango=True):
    """
        Return a string in plain English (or whatever language being used) giving the special fields that may be used to call Track.format()
        If usePango is True, the returned string uses Pango formatting for better presentation
    """
    if usePango: return '\n'.join(['<tt><b>%s</b></tt> %s' % (field.ljust(14), desc) for (field, desc) in FIELDS])
    else:        return '\n'.join(['%s\t%s' % (field.ljust(14), desc) for (field, desc) in FIELDS])


class Track:
    """ A track and its associated tags """

    def __init__(self, resource=None, scheme=None):
        """ Constructor """
        self.tags = {}

        if scheme is not None:   self.tags[TAG_SCH] = scheme
        if resource is not None: self.tags[TAG_RES] = resource


    def setNumber(self, nb):               self.tags[TAG_NUM] = nb
    def setTitle(self, title):             self.tags[TAG_TIT] = title
    def setArtist(self, artist):           self.tags[TAG_ART] = artist
    def setAlbum(self, album):             self.tags[TAG_ALB] = album
    def setLength(self, length):           self.tags[TAG_LEN] = length
    def setAlbumArtist(self, albumArtist): self.tags[TAG_AAR] = albumArtist
    def setDiscNumber(self, discNumber):   self.tags[TAG_DNB] = discNumber
    def setGenre(self, genre):             self.tags[TAG_GEN] = genre
    def setDate(self, date):               self.tags[TAG_DAT] = date
    def setMBTrackId(self, id):            self.tags[TAG_MBT] = id
    def setBitrate(self, bitrate):         self.tags[TAG_BTR] = bitrate
    def setSampleRate(self, sampleRate):   self.tags[TAG_SMP] = sampleRate
    def setVariableBitrate(self):          self.tags[TAG_MOD] = 1


    def __get(self, tag, defaultValue):
        """Return the value of tag if it exists, or return defaultValue

        We cannot set self.__get to point to self.tags.get, because the Track
        object has to be pickled.
        """
        return self.tags.get(tag, defaultValue)


    def getFilePath(self):    return self.tags[TAG_RES]
    def getNumber(self):      return self.__get(TAG_NUM, consts.UNKNOWN_TRACK_NUMBER)
    def getTitle(self):       return self.__get(TAG_TIT, self.getBasename())
    def getArtist(self):      return self.__get(TAG_ART, consts.UNKNOWN_ARTIST)
    def getAlbum(self):       return self.__get(TAG_ALB, consts.UNKNOWN_ALBUM)
    def getLength(self):      return self.__get(TAG_LEN, consts.UNKNOWN_LENGTH)
    def getAlbumArtist(self): return self.__get(TAG_AAR, consts.UNKNOWN_ALBUM_ARTIST)
    def getDiscNumber(self):  return self.__get(TAG_DNB, consts.UNKNOWN_DISC_NUMBER)
    def getGenre(self):       return self.__get(TAG_GEN, consts.UNKNOWN_GENRE)
    def getDate(self):        return self.__get(TAG_DAT, consts.UNKNOWN_DATE)
    def getEncMode(self):     return self.__get(TAG_MOD, consts.UNKNOWN_ENC_MODE)
    def getMBTrackId(self):   return self.__get(TAG_MBT, consts.UNKNOWN_MB_TRACKID)

    def getBitrate(self):
        """ Transform the bit rate into a string """
        bitrate = self.__get(TAG_BTR, consts.UNKNOWN_BITRATE)

        if bitrate == -1:            return _('unknown')
        elif self.getEncMode() == 1: return '~ %u kbps' % (bitrate // 1000)
        else:                        return '%u kbps'   % (bitrate // 1000)

    def getSampleRate(self):
        """ Transform the sample rate into a string"""
        return '%.1f kHz' % (self.__get(TAG_SMP, consts.UNKNOWN_SAMPLE_RATE) / 1000.0)


    def getURI(self):
        """ Return the complete URI to the resource """
        try:    return self.tags[TAG_SCH] + '://' + self.tags[TAG_RES]
        except: raise RuntimeError('The track is an unknown type of resource')


    def getFilename(self):
        """ Return the filename only, not the full path """
        return os.path.split(self.tags[TAG_RES])[1]


    def getExtendedAlbum(self):
        """ Return the album name plus the disc number, if any """
        if self.getDiscNumber() != consts.UNKNOWN_DISC_NUMBER:
            return _('%(album)s  [Disc %(discnum)u]') % {'album': self.getAlbum(), 'discnum': self.getDiscNumber()}
        else:
            return self.getAlbum()


    def __str__(self):
        """ String representation """
        return '%s - %s - %s (%u)' % (self.getArtist(), self.getAlbum(), self.getTitle(), self.getNumber())


    def format(self, fmtString):
        """ Replace the special fields in the given string by their corresponding value """
        result = fmtString

        result = result.replace( '{path}',         self.getFilePath()         )
        result = result.replace( '{album}',        self.getAlbum()            )
        result = result.replace( '{track}',        str(self.getNumber())      )
        result = result.replace( '{title}',        self.getTitle()            )
        result = result.replace( '{artist}',       self.getArtist()           )
        result = result.replace( '{genre}',        self.getGenre()            )
        result = result.replace( '{date}',         str(self.getDate())        )
        result = result.replace( '{disc}',         str(self.getDiscNumber())  )
        result = result.replace( '{bitrate}',      self.getBitrate()          )
        result = result.replace( '{sample_rate}',  str(self.getSampleRate())  )
        result = result.replace( '{duration_sec}', str(self.getLength())      )
        result = result.replace( '{duration_str}', sec2str(self.getLength())  )

        return result


    def formatHTMLSafe(self, fmtString):
        """
            Replace the special fields in the given string by their corresponding value
            Also ensure that the fields don't contain HTML special characters (&, <, >)
        """
        result = fmtString

        result = result.replace( '{path}',         tools.htmlEscape(self.getFilePath()) )
        result = result.replace( '{album}',        tools.htmlEscape(self.getAlbum())    )
        result = result.replace( '{track}',        str(self.getNumber())                )
        result = result.replace( '{title}',        tools.htmlEscape(self.getTitle())    )
        result = result.replace( '{artist}',       tools.htmlEscape(self.getArtist())   )
        result = result.replace( '{genre}',        tools.htmlEscape(self.getGenre())    )
        result = result.replace( '{date}',         str(self.getDate())                  )
        result = result.replace( '{disc}',         str(self.getDiscNumber())            )
        result = result.replace( '{bitrate}',      self.getBitrate()                    )
        result = result.replace( '{sample_rate}',  self.getSampleRate()                 )
        result = result.replace( '{duration_sec}', str(self.getLength())                )
        result = result.replace( '{duration_str}', sec2str(self.getLength())            )

        return result


    def __addIfKnown(self, dic, key, tag, unknownValue):
        """ This is an helper function used by the getMPRISMetadata() function  """
        value = self.__get(tag, unknownValue)
        if value != unknownValue:
            dic[key] = value


    def getMPRISMetadata(self):
        """ Return a dictionary with all available data in an MPRIS-compatible format """
        data = {'location': self.getURI()}

        self.__addIfKnown(data, 'tracknumber',      TAG_NUM, consts.UNKNOWN_TRACK_NUMBER)
        self.__addIfKnown(data, 'title',            TAG_TIT, consts.UNKNOWN_TITLE)
        self.__addIfKnown(data, 'time',             TAG_LEN, consts.UNKNOWN_LENGTH)
        self.__addIfKnown(data, 'artist',           TAG_ART, consts.UNKNOWN_ARTIST)
        self.__addIfKnown(data, 'album',            TAG_ALB, consts.UNKNOWN_ALBUM)
        self.__addIfKnown(data, 'mb track id',      TAG_MBT, consts.UNKNOWN_MB_TRACKID)
        self.__addIfKnown(data, 'genre',            TAG_GEN, consts.UNKNOWN_GENRE)
        self.__addIfKnown(data, 'date',             TAG_DAT, consts.UNKNOWN_DATE)
        self.__addIfKnown(data, 'audio-bitrate',    TAG_BTR, -1)
        self.__addIfKnown(data, 'audio-samplerate', TAG_SMP, consts.UNKNOWN_SAMPLE_RATE)

        # 'mtime' must be in milliseconds
        if 'time' in data:
            data['mtime'] = data['time'] * 1000

        return data


    def get_label(self, parent_label=None, playing=False):
        """
        Return a treeview representation
        """
        title = self.tags.get(TAG_TIT, '')
        artist = self.tags.get(TAG_ART, '')

        album = self.getExtendedAlbum()
        if album == consts.UNKNOWN_ALBUM:
            album = ''

        number = self.tags.get(TAG_NUM, '')
        length = self.getLength()

        if number:
            number = str(number).zfill(2)

        # Delete whitespace at the end
        connectors = ['the', 'and', '&', ',', '.', '?', '!', "'", ':', '-', ' ']

        if parent_label:
            parent_label = parent_label.lower()
            short_album = album.lower()
            short_artist = artist.lower()
            for connector in connectors:
                parent_label = parent_label.replace(connector, '')
                short_album = short_album.replace(connector, '')
                short_artist = short_artist.replace(connector, '')
            if short_album.strip() in parent_label:
                album = ''
            if short_artist.strip() in parent_label:
                artist = ''

        if title:
            label = ' - '.join([part for part in [artist, album, number, title] if part])
        else:
            label = self.getBasename()

        label = tools.htmlEscape(label)
        if playing:
            label = '<b>%s</b>' % label
        #label += ' <span foreground="gray">[%s]</span>' % tools.sec2str(length)
        label += ' [%s]' % tools.sec2str(length)
        return label

    def getBasename(self):
        name, ext = os.path.splitext(self.getFilename())
        return name

    def get_window_title(self):
        title = self.tags.get(TAG_TIT, '')
        artist = self.tags.get(TAG_ART, '')

        if not title:
            return self.getBasename()
        return ' - '.join([part for part in [artist, title] if part])

    def get_search_text(self):
        return '|||'.join([self.getFilePath(), self.tags.get(TAG_TIT, ''),
                           self.tags.get(TAG_ART, ''), self.getExtendedAlbum(),
                           str(self.getLength()), str(self.tags.get(TAG_NUM, ''))]).lower()

    def __repr__(self):
        return '<Track %s>' % self.get_window_title()
