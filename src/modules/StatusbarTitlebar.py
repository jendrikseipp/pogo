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

import modules, tools

from tools   import consts,  prefs
from gettext import ngettext, gettext  as _

MOD_INFO = ('Status and Title Bars', 'Status and Title Bars', '', [], True, False)


class StatusbarTitlebar(modules.Module):
    """ This module manages both the status and the title bars """

    def __init__(self):
        """ Constructor """
        modules.Module.__init__(self, (consts.MSG_EVT_NEW_TRACKLIST, consts.MSG_EVT_NEW_TRACK, consts.MSG_EVT_STOPPED,
                                       consts.MSG_EVT_APP_STARTED,   consts.MSG_EVT_PAUSED,    consts.MSG_EVT_UNPAUSED))


    def onAppStarted(self):
        """ Real initialization function, called when this module has been loaded """
        self.title     = consts.appName
        self.window    = prefs.getWidgetsTree().get_widget('win-main')
        self.statusbar = prefs.getWidgetsTree().get_widget('statusbar')
        self.contextId = self.statusbar.get_context_id('tracklist info')
        # Initial status
        self.onNewTracklist(0, 0)
        self.onNewTrack(None)


    def onNewTracklist(self, count, playtime):
        """ A new tracklist has been set """
        if count == 0:
            text = ''
        else:
            text = ngettext('One track in playlist  [%(length)s]', '%(count)u tracks in playlist  [%(length)s]', count) \
                    % {'count': count, 'length': tools.sec2str(playtime)}

        self.statusbar.pop(self.contextId)
        self.statusbar.push(self.contextId, text)


    def onNewTrack(self, track):
        """ A new track is being played, None if none """
        if track is None: self.title = consts.appName
        else:             self.title = '%s - %s' % (track.getArtist(), track.getTitle())

        self.window.set_title(self.title)


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this module """
        if   msg == consts.MSG_EVT_PAUSED:        self.window.set_title('%s %s' % (self.title, _('[paused]')))
        elif msg == consts.MSG_EVT_STOPPED:       self.onNewTrack(None)
        elif msg == consts.MSG_EVT_UNPAUSED:      self.window.set_title(self.title)
        elif msg == consts.MSG_EVT_NEW_TRACK:     self.onNewTrack(params['track'])
        elif msg == consts.MSG_EVT_APP_STARTED:   self.onAppStarted()
        elif msg == consts.MSG_EVT_NEW_TRACKLIST: self.onNewTracklist(len(params['tracks']), params['playtime'])
