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

import dbus, dbus.service, gobject, media, modules, traceback

from tools import consts, log

MOD_INFO = ('D-Bus Support', 'D-Bus Support', '', [], True, False)


# MPRIS caps constants
CAPS_CAN_GO_NEXT          =  1
CAPS_CAN_GO_PREV          =  2
CAPS_CAN_PAUSE            =  4
CAPS_CAN_PLAY             =  8
CAPS_CAN_SEEK             = 16
CAPS_CAN_PROVIDE_METADATA = 32
CAPS_CAN_HAS_TRACKLIST    = 64


class DBus(modules.Module):
    """ Enable D-Bus support """

    def __init__(self):
        """ Constructor """
        modules.Module.__init__(self, (consts.MSG_EVT_APP_STARTED, consts.MSG_EVT_NEW_TRACK, consts.MSG_EVT_STOPPED, consts.MSG_EVT_VOLUME_CHANGED,
                                       consts.MSG_EVT_TRACK_POSITION, consts.MSG_EVT_PAUSED, consts.MSG_EVT_UNPAUSED, consts.MSG_EVT_NEW_TRACKLIST,
                                       consts.MSG_EVT_TRACK_MOVED, consts.MSG_EVT_REPEAT_CHANGED))

    def getMPRISCaps(self):
        """ Return an integer sticking to the MPRIS caps definition """
        caps = CAPS_CAN_HAS_TRACKLIST

        if len(self.tracklist) != 0:
            caps |= CAPS_CAN_PLAY

        if self.currTrack is not None:
            caps |= CAPS_CAN_PAUSE
            caps |= CAPS_CAN_SEEK
            caps |= CAPS_CAN_PROVIDE_METADATA

            if self.canGoNext: caps |= CAPS_CAN_GO_NEXT
            if self.canGoPrev: caps |= CAPS_CAN_GO_PREV

        return caps


    def getMPRISStatus(self):
        """ Return a tuple sticking to the MPRIS status definition """
        if self.currTrack is None: playStatus = 2
        elif self.paused:          playStatus = 1
        else:                      playStatus = 0

        if self.repeat: repeatStatus = 1
        else:           repeatStatus = 0

        return (playStatus, 0, 0, repeatStatus)


    def onAppStarted(self):
        """ Initialize this module """
        self.repeat       = False
        self.paused       = False
        self.tracklist    = []
        self.currTrack    = None
        self.canGoNext    = False
        self.canGoPrev    = False
        self.currVolume   = 0
        self.currPosition = 0

        try:
            self.sessionBus = dbus.SessionBus()
            self.busName    = dbus.service.BusName(consts.dbusService, bus=self.sessionBus)

            # Create the three MPRIS objects
            self.busObjectRoot      = DBusObjectRoot(self.busName, self)
            self.busObjectPlayer    = DBusObjectPlayer(self.busName, self)
            self.busObjectTracklist = DBusObjectTracklist(self.busName, self)
        except:
            self.sessionBus = None
            log.logger.error('[%s] Error while initializing\n\n%s' % (MOD_INFO[modules.MODINFO_NAME], traceback.format_exc()))


    def onNewTrack(self, track):
        """ A new track is being played """
        self.paused    = False
        self.currTrack = track
        self.busObjectPlayer.CapsChange(self.getMPRISCaps())
        self.busObjectPlayer.TrackChange(track.getMPRISMetadata())
        self.busObjectPlayer.StatusChange(self.getMPRISStatus())


    def onStopped(self):
        """ Playback is stopped """
        self.paused       = False
        self.currTrack    = None
        self.currPosition = 0
        self.busObjectPlayer.CapsChange(self.getMPRISCaps())
        self.busObjectPlayer.StatusChange(self.getMPRISStatus())


    def onVolumeChanged(self, volume):
        """ The volume has been changed """
        self.currVolume = volume


    def onNewTrackPosition(self, position):
        """ New position in the current track """
        self.currPosition = position


    def onPaused(self):
        """ The playback has been paused """
        self.paused = True
        self.busObjectPlayer.StatusChange(self.getMPRISStatus())


    def onUnpaused(self):
        """ The playback has been unpaused """
        self.paused = False
        self.busObjectPlayer.StatusChange(self.getMPRISStatus())


    def onNewTracklist(self, tracks):
        """ A new tracklist has been set """
        self.tracklist = tracks
        self.busObjectPlayer.CapsChange(self.getMPRISCaps())
        self.busObjectTracklist.TrackListChange(len(tracks))


    def onCurrentTrackMoved(self, canGoNext, canGoPrev):
        """ The position of the current track has moved in the playlist """
        self.canGoNext = canGoNext
        self.canGoPrev = canGoPrev
        self.busObjectPlayer.CapsChange(self.getMPRISCaps())


    def onRepeatChanged(self, repeat):
        """ Repeat has been enabled/disabled """
        self.repeat = repeat
        self.busObjectPlayer.StatusChange(self.getMPRISStatus())


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this module """
        if msg == consts.MSG_EVT_APP_STARTED:
            self.onAppStarted()
        elif self.sessionBus is not None:
            if   msg == consts.MSG_EVT_PAUSED:         self.onPaused()
            elif msg == consts.MSG_EVT_STOPPED:        self.onStopped()
            elif msg == consts.MSG_EVT_UNPAUSED:       self.onUnpaused()
            elif msg == consts.MSG_EVT_NEW_TRACK:      self.onNewTrack(params['track'])
            elif msg == consts.MSG_EVT_TRACK_MOVED:    self.onCurrentTrackMoved(params['hasNext'], params['hasPrevious'])
            elif msg == consts.MSG_EVT_NEW_TRACKLIST:  self.onNewTracklist(params['tracks'])
            elif msg == consts.MSG_EVT_VOLUME_CHANGED: self.onVolumeChanged(params['value'])
            elif msg == consts.MSG_EVT_TRACK_POSITION: self.onNewTrackPosition(params['seconds'])
            elif msg == consts.MSG_EVT_REPEAT_CHANGED: self.onRepeatChanged(params['repeat'])



class DBusObjectRoot(dbus.service.Object):

    def __init__(self, busName, module):
        """ Constructor """
        dbus.service.Object.__init__(self, busName, '/')


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='s')
    def Identity(self):
        """ Returns a string containing the media player identification """
        return '%s %s' % (consts.appName, consts.appVersion)


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='')
    def Quit(self):
        """ Makes the media player exit """
        modules.postQuitMsg()


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='(qq)')
    def MprisVersion(self):
        """ Returns a struct that represents the version of the MPRIS spec being implemented """
        return (1, 0)



class DBusObjectTracklist(dbus.service.Object):

    def __init__(self, busName, module):
        """ Constructor """
        self.module = module
        dbus.service.Object.__init__(self, busName, '/TrackList')


    @dbus.service.method(consts.dbusInterface, in_signature='i', out_signature='a{sv}')
    def GetMetadata(self, idx):
        """ Gives all meta data available for element at given position in the TrackList, counting from 0 """
        if idx >= 0 and idx < len(self.module.tracklist): return self.module.tracklist[idx].getMPRISMetadata()
        else:                                             return {}


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='i')
    def GetCurrentTrack(self):
        """ Return the position of current URI in the TrackList """
        if self.module.currTrack is None: return -1
        else:                             return self.module.currTrack.getPlaylistPos()-1


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='i')
    def GetLength(self):
        """ Number of elements in the TrackList """
        return len(self.module.tracklist)


    @dbus.service.method(consts.dbusInterface, in_signature='sb', out_signature='i')
    def AddTrack(self, uri, playNow):
        """ Appends an URI in the TrackList """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_TRACKLIST_ADD, {'tracks': [media.getTrackFromFile(uri)], 'playNow': playNow})
        return 0


    @dbus.service.method(consts.dbusInterface, in_signature='i', out_signature='')
    def DelTrack(self, idx):
        """ Removes an URI from the TrackList """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_TRACKLIST_DEL, {'idx': idx})


    @dbus.service.method(consts.dbusInterface, in_signature='b', out_signature='')
    def SetLoop(self, loop):
        """ Toggle playlist loop """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_TRACKLIST_REPEAT, {'repeat': loop})


    @dbus.service.method(consts.dbusInterface, in_signature='b', out_signature='')
    def SetRandom(self, random):
        """ Toggle playlist shuffle / random """
        if random:
            gobject.idle_add(modules.postMsg, consts.MSG_CMD_TRACKLIST_SHUFFLE)


    @dbus.service.signal(consts.dbusInterface, signature='i')
    def TrackListChange(self, length):
        """ Signal is emitted when the tracklist content has changed """
        pass


    # These functions are not part of the MPRIS, but are useful


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='')
    def Clear(self):
        """ Clear the tracklist """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_TRACKLIST_CLR)


    @dbus.service.method(consts.dbusInterface, in_signature='asb', out_signature='')
    def AddTracks(self, uris, playNow):
        """ Appends multiple URIs to the tracklist """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_TRACKLIST_ADD, {'tracks': media.getTracks([file for file in uris]), 'playNow': playNow})


    @dbus.service.method(consts.dbusInterface, in_signature='asb', out_signature='')
    def SetTracks(self, uris, playNow):
        """ Replace the tracklist by the given URIs """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_TRACKLIST_SET, {'tracks': media.getTracks([file for file in uris]), 'playNow': playNow})



class DBusObjectPlayer(dbus.service.Object):

    def __init__(self, busName, module):
        """ Constructor """
        self.module = module
        dbus.service.Object.__init__(self, busName, '/Player')


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='')
    def Next(self):
        """ Goes to the next element """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_NEXT)


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='')
    def Prev(self):
        """ Goes to the previous element """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_PREVIOUS)


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='')
    def Pause(self):
        """ If playing : pause. If paused : unpause """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_TOGGLE_PAUSE)


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='')
    def Stop(self):
        """ Stop playing """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_STOP)


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='')
    def Play(self):
        """ If playing : rewind to the beginning of current track, else : start playing """
        if len(self.module.tracklist) != 0:
            if self.module.currTrack is None: gobject.idle_add(modules.postMsg, consts.MSG_CMD_TOGGLE_PAUSE)
            else:                             gobject.idle_add(modules.postMsg, consts.MSG_CMD_SEEK, {'seconds': 0})


    @dbus.service.method(consts.dbusInterface, in_signature='b', out_signature='')
    def Repeat(self, repeat):
        """ Toggle the current track repeat """
        # We don't support repeating only the current track
        pass


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='(iiii)')
    def GetStatus(self):
        """ Return the status of media player as a struct of 4 ints """
        return self.module.getMPRISStatus()


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='a{sv}')
    def GetMetadata(self):
        """ Gives all meta data available for the currently played element """
        if self.module.currTrack is None: return {}
        else:                             return self.module.currTrack.getMPRISMetadata()


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='i')
    def GetCaps(self):
        """ Return the media player's current capabilities """
        return self.module.getMPRISCaps()


    @dbus.service.method(consts.dbusInterface, in_signature='i', out_signature='')
    def VolumeSet(self, volume):
        """ Sets the volume (argument must be in [0;100]) """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_SET_VOLUME, {'value': volume / 100.0})


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='i')
    def VolumeGet(self):
        """ Returns the current volume (must be in [0;100]) """
        return self.module.currVolume * 100


    @dbus.service.method(consts.dbusInterface, in_signature='i', out_signature='')
    def PositionSet(self, position):
        """ Sets the playing position (argument must be in [0;<track_length>] in milliseconds) """
        gobject.idle_add(modules.postMsg, consts.MSG_CMD_SEEK, {'seconds': position / 1000})


    @dbus.service.method(consts.dbusInterface, in_signature='', out_signature='i')
    def PositionGet(self):
        """ Returns the playing position (will be [0;<track_length>] in milliseconds) """
        return self.module.currPosition * 1000


    @dbus.service.signal(consts.dbusInterface, signature='a{sv}')
    def TrackChange(self, metadata):
        """ Signal is emitted when the media player plays another track """
        pass


    @dbus.service.signal(consts.dbusInterface, signature='(iiii)')
    def StatusChange(self, status):
        """ Signal is emitted when the status of the media player change """
        pass


    @dbus.service.signal(consts.dbusInterface, signature='i')
    def CapsChange(self, caps):
        """ Signal is emitted when the media player changes capabilities """
        pass
