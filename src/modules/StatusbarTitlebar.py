# -*- coding: utf-8 -*-
#
# Authors: Ingelrest François (Francois.Ingelrest@gmail.com)
#          Jendrik Seipp (jendrikseipp@web.de)
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
from gettext import ngettext, gettext as _

MOD_INFO = ('Status and Title Bars', 'Status and Title Bars', '', [], True, False)


class StatusbarTitlebar(modules.Module):
    """ This module manages both the status and the title bars """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_PAUSED:            self.onPaused,
                        consts.MSG_EVT_STOPPED:           self.onStopped,
                        consts.MSG_EVT_UNPAUSED:          self.onUnpaused,
                        consts.MSG_EVT_NEW_TRACK:         self.onNewTrack,
                        consts.MSG_EVT_APP_STARTED:       self.onAppStarted,
                        consts.MSG_EVT_NEW_TRACKLIST:     self.onNewTracklist,
                        ##consts.MSG_EVT_TRACKLIST_NEW_SEL: self.onNewSelection,
                   }

        modules.Module.__init__(self, handlers)


    def __updateTitlebar(self):
        """ Update the title bar """
        if self.currTrack is None: self.window.set_title(consts.appName)
        elif self.paused:          self.window.set_title('%s %s' % (self.currTrack.get_window_title(), _('[paused]')))
        else:                      self.window.set_title('%s' % self.currTrack.get_window_title())


    def __updateStatusbar(self):
        """ Update the status bar """
        # Statusbar may be disabled
        if not self.status1:
            return
            
        # Tracklist
        count = len(self.tracklist)
        if count == 0:
            self.status1.set_label('')
        else:
            self.status1.set_label(ngettext('One track in playlist  [%(length)s]', '%(count)u tracks in playlist  [%(length)s]', count) \
                                      % {'count': count, 'length': tools.sec2str(self.playtime)})

        # Selected tracks
        count = len(self.selTracks)
        if count == 0:
            self.status2.set_label('')
        else:
            selection = ngettext('One track selected', '%(count)u tracks selected', count) % {'count': count}

            audioType = self.selTracks[0].getType()
            for track in self.selTracks[1:]:
                if track.getType() != audioType:
                    audioType = _('various')
                    break

            bitrate = self.selTracks[0].getBitrate()
            for track in self.selTracks[1:]:
                if track.getBitrate() != bitrate:
                    bitrate = _('various')
                    break

            self.status2.set_label(_('%(selection)s (Type: %(type)s, Bitrate: %(bitrate)s)') % {'selection': selection, 'type': audioType, 'bitrate': bitrate})


    # --== Message handlers ==--


    def onAppStarted(self):
        """ Real initialization function, called when this module has been loaded """
        self.window  = prefs.getWidgetsTree().get_widget('win-main')
        self.status1 = prefs.getWidgetsTree().get_widget('lbl-status1')
        self.status2 = prefs.getWidgetsTree().get_widget('lbl-status2')

        # Current player status
        self.paused    = False
        self.playtime  = 0
        self.tracklist = []
        self.selTracks = []
        self.currTrack = None


    def onNewTrack(self, track):
        """ A new track is being played """
        self.paused    = False
        self.currTrack = track
        self.__updateTitlebar()


    def onPaused(self):
        """ Playback has been paused """
        self.paused = True
        self.__updateTitlebar()


    def onUnpaused(self):
        """ Playback has been unpaused """
        self.paused = False
        self.__updateTitlebar()


    def onStopped(self):
        """ Playback has been stopped """
        self.paused    = False
        self.currTrack = None
        self.__updateTitlebar()


    def onNewTracklist(self, tracks, playtime):
        """ A new tracklist has been set """
        self.playtime  = playtime
        self.tracklist = tracks
        self.__updateStatusbar()


    def onNewSelection(self, tracks):
        """ A new set of track has been selected """
        self.selTracks = tracks
        self.__updateStatusbar()
