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

import gobject, modules, os.path

from time  import time
from tools import consts, prefs
from media import audioplayer


MOD_INFO           = ('GStreamer Player', 'GStreamer Player', '', [], True, False)
MIN_PLAYBACK_DELAY = 1.5


class GSTPlayer(modules.Module):
    """ This module is the 'real' GStreamer player """

    def __init__(self):
        """ Constructor """
        # The player must be created during the application startup, not when the application is ready (MSG_EVT_APP_STARTED)
        self.player = audioplayer.AudioPlayer(self.__onTrackEnded, not prefs.getCmdLine()[0].playbin)

        modules.Module.__init__(self, (consts.MSG_CMD_PLAY,   consts.MSG_CMD_SET_VOLUME,   consts.MSG_CMD_ENABLE_RG,
                                       consts.MSG_CMD_SEEK,   consts.MSG_EVT_APP_STARTED,  consts.MSG_CMD_DISABLE_RG,
                                       consts.MSG_CMD_STOP,   consts.MSG_CMD_TOGGLE_PAUSE, consts.MSG_CMD_ENABLE_EQZ,
                                       consts.MSG_CMD_BUFFER, consts.MSG_CMD_SET_EQZ_LVLS, consts.MSG_CMD_STEP,
                                       consts.MSG_CMD_SET_CD_SPEED))

    def onAppStarted(self):
        """ This is the real initialization function, called when this module has been loaded """
        self.nextURI       = None
        self.queuedSeek    = None
        self.updateTimer   = None
        self.lastPlayback  = 0
        self.playbackTimer = None


    def updateTimerHandler(self):
        """ Regularly called during playback (can be paused) """
        if self.player.isPlaying():
            position  = self.player.getPosition()
            remaining = self.player.getDuration() - position

            modules.postMsg(consts.MSG_EVT_TRACK_POSITION, {'seconds': int(position / 1000000000)})

            if remaining < 4000000000 and self.nextURI is None and not prefs.getCmdLine()[0].playbin:
                modules.postMsg(consts.MSG_EVT_NEED_BUFFER)

        return True


    def __startUpdateTimer(self):
        """ Start the update timer if needed """
        if self.updateTimer is None:
            self.updateTimer = gobject.timeout_add(1000, self.updateTimerHandler)


    def __stopUpdateTimer(self):
        """ Start the update timer if needed """
        if self.updateTimer is not None:
            gobject.source_remove(self.updateTimer)
            self.updateTimer = None


    def bufferNextTrack(self, uri):
        """ Buffer the next track """
        if self.nextURI is None and not prefs.getCmdLine()[0].playbin:
            self.nextURI = uri
            self.player.setNextURI(uri)


    def __onTrackEnded(self, error):
        """ Called to signal eos and errors """
        if error: modules.postMsg(consts.MSG_EVT_TRACK_ENDED_ERROR)
        else:     modules.postMsg(consts.MSG_EVT_TRACK_ENDED_OK)


    def __playbackTimerHandler(self):
        """ Switch the player to playback mode, and start the update timer """
        if not self.player.isPlaying():
            self.player.play()

        self.nextURI       = None
        self.lastPlayback  = time()
        self.playbackTimer = None

        self.__startUpdateTimer()

        return False


    def play(self, uri):
        """ Play the given URI """
        if uri != self.nextURI:
            self.player.stop()
            self.player.setURI(uri)
            self.__stopUpdateTimer()

        elapsed = time() - self.lastPlayback

        # Looks like GStreamer can be pretty much fucked if we start/stop the pipeline too quickly (e.g., when clicking "next" very fast)
        # We minimize the load in these extreme cases by ensuring that at least one second has elapsed since the last playback
        # Note that this delay is avoided when tracks are chained, since the playback of the next track has then already started (uri == self.nextURI)
        if elapsed >= MIN_PLAYBACK_DELAY:
            self.__playbackTimerHandler()
        else:
            if self.playbackTimer is not None:
                gobject.source_remove(self.playbackTimer)
            self.playbackTimer = gobject.timeout_add(int((MIN_PLAYBACK_DELAY - elapsed) * 1000), self.__playbackTimerHandler)


    def stop(self):
        """ Stop playing """
        self.__stopUpdateTimer()
        self.player.stop()
        self.nextURI = None
        self.player.clearNextURI()

        if self.playbackTimer is not None:
            gobject.source_remove(self.playbackTimer)

        modules.postMsg(consts.MSG_EVT_STOPPED)


    def togglePause(self):
        """ Switch between play/pause """
        if self.player.isPaused():
            if self.queuedSeek is not None:
                self.player.seek(self.queuedSeek*1000000000)
                self.queuedSeek = None
            self.player.play()
            modules.postMsg(consts.MSG_EVT_UNPAUSED)
        elif self.player.isPlaying():

            if self.playbackTimer is not None:
                gobject.source_remove(self.playbackTimer)

            self.player.pause()
            modules.postMsg(consts.MSG_EVT_PAUSED)


    def seek(self, seconds):
        """ Jump to the given position if playing, or buffer it if paused """
        if   self.player.isPaused():  self.queuedSeek = seconds
        elif self.player.isPlaying(): self.player.seek(seconds*1000000000)


    def step(self, seconds):
        """ Step back or forth """
        if self.player.isPlaying():
            newPos = self.player.getPosition() + (seconds * 1000000000)

            if newPos < 0:
                self.player.seek(0)
                self.updateTimerHandler()
            elif newPos < self.player.getDuration():
                self.player.seek(newPos)
                self.updateTimerHandler()


    def setVolume(self, value):
        """ Change the volume """
        self.player.setVolume(value)
        modules.postMsg(consts.MSG_EVT_VOLUME_CHANGED, {'value': value})


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this module """
        if   msg == consts.MSG_CMD_STOP:         self.stop()
        elif msg == consts.MSG_CMD_PLAY:         self.play(params['uri'])
        elif msg == consts.MSG_CMD_SEEK:         self.seek(params['seconds'])
        elif msg == consts.MSG_CMD_STEP:         self.step(params['seconds'])
        elif msg == consts.MSG_CMD_BUFFER:       self.bufferNextTrack(params['uri'])
        elif msg == consts.MSG_CMD_ENABLE_RG:    self.player.enableReplayGain()
        elif msg == consts.MSG_CMD_DISABLE_RG:   self.player.disableReplayGain()
        elif msg == consts.MSG_CMD_SET_VOLUME:   self.setVolume(params['value'])
        elif msg == consts.MSG_EVT_APP_STARTED:  self.onAppStarted()
        elif msg == consts.MSG_CMD_ENABLE_EQZ:   self.player.enableEqualizer()
        elif msg == consts.MSG_CMD_SET_EQZ_LVLS: self.player.setEqualizerLvls(params['lvls'])
        elif msg == consts.MSG_CMD_TOGGLE_PAUSE: self.togglePause()
        elif msg == consts.MSG_CMD_SET_CD_SPEED: self.player.setCDReadSpeed(params['speed'])
