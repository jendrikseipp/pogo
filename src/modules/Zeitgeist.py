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

import modules, traceback

from tools     import consts
from gettext   import gettext as _
from tools.log import logger

MOD_INFO = ('Zeitgeist', 'Zeitgeist', _('Send track information to the Zeitgeist service'), ['zeitgeist'], False, False)


class Zeitgeist(modules.ThreadedModule):


    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_APP_QUIT:     self.onModUnloaded,
                        consts.MSG_EVT_NEW_TRACK:    self.onNewTrack,
                        consts.MSG_EVT_MOD_LOADED:   self.onModLoaded,
                        consts.MSG_EVT_APP_STARTED:  self.onModLoaded,
                        consts.MSG_EVT_MOD_UNLOADED: self.onModUnloaded,
                   }

        modules.ThreadedModule.__init__(self, handlers)


    # --== Message handlers ==--


    def onModLoaded(self):
        """ The module has been loaded """
        self.client = None

        try:
            from zeitgeist.client import ZeitgeistClient

            self.client = ZeitgeistClient()
        except:
            logger.info('[%s] Could not create Zeitgeist client\n\n%s' % (MOD_INFO[modules.MODINFO_NAME], traceback.format_exc()))


    def onModUnloaded(self):
        """ The module has been unloaded """
        self.client = None


    def onNewTrack(self, track):
        """ Send track information to Zeitgeist """
        import mimetypes, os.path

        from zeitgeist.datamodel import Event, Subject, Interpretation, Manifestation

        mime, encoding = mimetypes.guess_type(track.getFilePath(), strict=False)
        
        title = track.getTitle()
        album = track.getAlbum()
        artist = track.getArtist()
        
        # Handle "unknown" tags
        if 'unknown' in title.lower():
            title = track.get_basename()
        if 'unknown' in album.lower():
            album = ''
        if 'unknown' in artist.lower():
            album = ''
            
        parts = [artist, album]
        text = ' - '.join([part for part in parts if part])

        subject = Subject.new_for_values(
            uri            = os.path.dirname(track.getURI()),
            #text           = track.getTitle() + ' - ' + track.getArtist() + ' - ' + track.getExtendedAlbum(),
            text           = text,
            mimetype       = mime,
            manifestation  = unicode(Manifestation.FILE_DATA_OBJECT),
            interpretation = unicode(Interpretation.AUDIO),
        )

        if hasattr(Interpretation, 'ACCESS_EVENT'):
            eventType = Interpretation.ACCESS_EVENT
        else:
            eventType = Interpretation.OPEN_EVENT

        event = Event.new_for_values(
            actor          = "application://pogo.desktop",
            subjects       = [subject,],
            interpretation = eventType,
        )

        self.client.insert_event(event)
