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

from gettext import gettext as _
import time
import traceback

import modules
from tools import consts
from tools.log import logger

MOD_INFO = ('Zeitgeist', 'Zeitgeist', _('Send track information to the Zeitgeist service'), ['zeitgeist'], True, False)


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
            from zeitgeist.datamodel import Event

            self.client = ZeitgeistClient()
            if self.client.get_version() >= [0, 3, 2, 999]:
                self.client.register_data_source("Pogo", "Pogo", "Play your music",
                            [Event.new_for_values(actor="application://pogo.desktop")])
        except:
            logger.info('[%s] Could not create Zeitgeist client\n\n%s' % (MOD_INFO[modules.MODINFO_NAME], traceback.format_exc()))


    def onModUnloaded(self):
        """ The module has been unloaded """
        self.client = None


    def onNewTrack(self, track):
        """ Send track information to Zeitgeist """
        if self.client is None:
            return

        from zeitgeist.datamodel import Interpretation

        if hasattr(Interpretation, 'ACCESS_EVENT'):
            event_type = Interpretation.ACCESS_EVENT
        else:
            event_type = Interpretation.OPEN_EVENT

        self.send_to_zeitgeist(track, event_type)


    def send_to_zeitgeist(self, track, event_type):
        """
        Other players (e.g. Rhythmbox) log the playing of individual files, but
        we want to log albums.

        Maybe it would be better to log individual files, but then we would have
        to distinguish between Manifestation.USER_ACTIVITY and
        Manifestation.SCHEDULED_ACTIVITY.

        Another possible addition would be logging Interpretation.LEAVE_EVENT.
        """
        import mimetypes, os.path

        from zeitgeist.datamodel import Event, Subject, Interpretation, Manifestation

        mime, encoding = mimetypes.guess_type(track.getFilePath(), strict=False)

        title = track.getTitle()
        album = track.getAlbum()
        artist = track.getArtist()
        uri = track.getURI()
        origin = os.path.dirname(uri)

        # Handle "unknown" tags
        if 'unknown' in title.lower():
            title = track.getBasename()
        if 'unknown' in album.lower():
            album = ''
        if 'unknown' in artist.lower():
            artist = ''

        subject = Subject.new_for_values(
            uri            = origin,
            text           = ' - '.join([part for part in [artist, album] if part]),
            mimetype       = mime,
            manifestation  = unicode(Manifestation.FILE_DATA_OBJECT),
            interpretation = unicode(Interpretation.AUDIO),
            origin         = origin,
        )

        event = Event.new_for_values(
            actor          = "application://pogo.desktop",
            subjects       = [subject,],
            interpretation = unicode(event_type),
            timestamp      = int(time.time() * 1000),
        )

        self.client.insert_event(event)
