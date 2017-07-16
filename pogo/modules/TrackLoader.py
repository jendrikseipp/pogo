# -*- coding: utf-8 -*-
#
# Copyright (c) 2012  Jendrik Seipp (jendrikseipp@web.de)
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

from pogo import modules
from pogo import media
from pogo.tools import consts


# Module information
MOD_INFO = ('TrackLoader', 'Load tracks from disk asynchronously', '', [], True, False)
MOD_NAME = MOD_INFO[modules.MODINFO_NAME]


class TrackLoader(modules.ThreadedModule):

    def __init__(self):
        handlers = {
            consts.MSG_EVT_LOAD_TRACKS: self.onLoadTracks,
        }
        modules.ThreadedModule.__init__(self, handlers)

    def onLoadTracks(self, paths):
        modules.postMsg(consts.MSG_CMD_TRACKLIST_ADD,
                        {'tracks': media.getTracks(paths), 'playNow': True})
