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

import media, modules, os.path, tools, traceback

from tools import consts, log, prefs

MOD_INFO = ('Command Line Support', 'Command Line Support', '', [], True, False)
MOD_NAME = MOD_INFO[modules.MODINFO_NAME]


class CommandLine(modules.ThreadedModule):

    def __init__(self):
        """ Constructor """
        modules.ThreadedModule.__init__(self, (consts.MSG_EVT_NEW_TRACKLIST, consts.MSG_EVT_APP_STARTED))


    def onAppStarted(self):
        """ Try to fill the playlist by using the files given on the command line or by restoring the last playlist """
        (options, args)    = prefs.getCmdLine()
        self.savedPlaylist = os.path.join(consts.dirCfg, 'saved-playlist.txt')

        if len(args) != 0:
            log.logger.info('[%s] Filling playlist with files given on command line' % MOD_NAME)
            modules.postMsg(consts.MSG_CMD_TRACKLIST_SET, {'tracks': media.getTracks(args), 'playNow': True})
        else:
            try:
                tracks = [media.track.unserialize(serialTrack) for serialTrack in tools.pickleLoad(self.savedPlaylist)]
                modules.postMsg(consts.MSG_CMD_TRACKLIST_SET, {'tracks': tracks, 'playNow': False})
                log.logger.info('[%s] Restored playlist' % MOD_NAME)
            except:
                log.logger.error('[%s] Unable to restore playlist from %s\n\n%s' % (MOD_NAME, self.savedPlaylist, traceback.format_exc()))


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this modules """
        if msg == consts.MSG_EVT_NEW_TRACKLIST:
            tools.pickleSave(self.savedPlaylist, [track.serialize() for track in params['tracks']])
        elif msg == consts.MSG_EVT_APP_STARTED:
            self.onAppStarted()
