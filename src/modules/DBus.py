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


class DBus(modules.Module):
    """ Enable D-Bus support """

    def __init__(self):
        """ Constructor """
        modules.Module.__init__(self, (consts.MSG_EVT_APP_STARTED, ))


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this module """
        if msg == consts.MSG_EVT_APP_STARTED:
            # Register this object to DBus
            try:
                self.sessionBus = dbus.SessionBus()
                self.busName    = dbus.service.BusName(consts.dbusService, bus=self.sessionBus)
                self.busObject  = DBusInterface(self.busName, self)
            except:
                self.sessionBus = None
                log.logger.error('[%s] Error while initializing\n\n%s' % (MOD_INFO[modules.MODINFO_NAME], traceback.format_exc()))


class DBusInterface(dbus.service.Object):

    def __init__(self, busName, module):
        """ Constructor """
        dbus.service.Object.__init__(self, busName, consts.dbusObject)

    @dbus.service.method(consts.dbusInterface, in_signature='uas', out_signature='b')
    def sendMsg(self, msg, params):
        """ Send the given message and its parameters to the core """
        if msg in (consts.MSG_CMD_TOGGLE_PAUSE,  consts.MSG_CMD_NEXT, consts.MSG_CMD_PREVIOUS, consts.MSG_CMD_STOP,
                   consts.MSG_CMD_TRACKLIST_CLR, consts.MSG_CMD_TRACKLIST_SHUFFLE):
            gobject.idle_add(modules.postMsg, msg)
        elif msg == consts.MSG_CMD_TRACKLIST_ADD:
            gobject.idle_add(modules.postMsg, msg, {'tracks': media.getTracks([file for file in params])})
        elif msg == consts.MSG_CMD_TRACKLIST_SET:
            gobject.idle_add(modules.postMsg, msg, {'tracks': media.getTracks([file for file in params]), 'playNow': True})
        elif msg == consts.MSG_CMD_SET_VOLUME:
            gobject.idle_add(modules.postMsg, msg, {'value': float(params[0]) / 100.0})
        elif msg == consts.MSG_CMD_BRING_TO_FRONT:
            gobject.idle_add(modules.postMsg, msg)
        else:
            return False

        return True
