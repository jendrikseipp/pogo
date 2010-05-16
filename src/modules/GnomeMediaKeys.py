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

import dbus, modules, time, traceback

from tools import consts, log

MOD_INFO = ('Gnome Media Keys', 'Gnome Media Keys', '', [], True, False)


(
    MK_OLD,        # Prior Gnome 2.22
    MK_GNOME_222,  # From Gnome 2.22
) = range(2)


class GnomeMediaKeys(modules.Module):
    """ Support for Gnome multimedia keys """

    def __init__(self):
        """ Constructor """
        modules.Module.__init__(self, (consts.MSG_EVT_APP_STARTED, consts.MSG_EVT_APP_QUIT))


    def handleMsg(self, msg, params):
        """ Handle messages sent to this modules """
        if msg == consts.MSG_EVT_APP_STARTED:
            # Gnome >= 2.22 uses different DBus session/interface for media keys (#208354)
            try:
                from gnome import gnome_python_version

                if gnome_python_version < (2, 22):
                    mkMode = MK_OLD
                else:
                    mkMode = MK_GNOME_222
            except:
                log.logger.info('[%s] Gnome does not seem to be running' % (MOD_INFO[modules.MODINFO_NAME]))
                return

            # Connect our own handler
            try:
                if mkMode == MK_OLD:
                    service = dbus.SessionBus().get_object('org.gnome.SettingsDaemon', '/org/gnome/SettingsDaemon')
                    self.dbusInterface = dbus.Interface(service, 'org.gnome.SettingsDaemon')
                else:
                    service = dbus.SessionBus().get_object('org.gnome.SettingsDaemon', '/org/gnome/SettingsDaemon/MediaKeys')
                    self.dbusInterface = dbus.Interface(service, 'org.gnome.SettingsDaemon.MediaKeys')

                self.dbusInterface.GrabMediaPlayerKeys(consts.appName, time.time())
                self.dbusInterface.connect_to_signal('MediaPlayerKeyPressed', self.onMediaKey)
            except:
                log.logger.error('[%s] Error while initializing\n\n%s' % (MOD_INFO[modules.MODINFO_NAME], traceback.format_exc()))
                self.dbusInterface = None
        elif msg == consts.MSG_EVT_APP_QUIT and self.dbusInterface is not None:
            self.dbusInterface.ReleaseMediaPlayerKeys(consts.appName)


    def onMediaKey(self, appName, action):
        """ A media key has been pressed """
        if appName == consts.appName:
            if action == 'Stop':              modules.postMsg(consts.MSG_CMD_STOP)
            elif action == 'Next':            modules.postMsg(consts.MSG_CMD_NEXT)
            elif action == 'Previous':        modules.postMsg(consts.MSG_CMD_PREVIOUS)
            elif action in ['Play', 'Pause']: modules.postMsg(consts.MSG_CMD_TOGGLE_PAUSE)
