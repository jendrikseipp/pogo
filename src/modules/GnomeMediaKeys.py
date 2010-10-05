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

import dbus, modules, traceback

from time  import time
from tools import consts, log

MOD_INFO = ('Gnome Media Keys', 'Gnome Media Keys', '', [], True, False)

# Generate a 'unique' application name so that multiple instances won't interfere with each other
APP_UID = consts.appName + str(time())


class GnomeMediaKeys(modules.Module):
    """ Support for Gnome multimedia keys """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_APP_QUIT:    self.onAppQuit,
                        consts.MSG_EVT_APP_STARTED: self.onAppStarted,
                   }

        modules.Module.__init__(self, handlers)


    def onMediaKey(self, appName, action):
        """ A media key has been pressed """
        if   action == 'Stop':            modules.postMsg(consts.MSG_CMD_STOP)
        elif action == 'Next':            modules.postMsg(consts.MSG_CMD_NEXT)
        elif action == 'Previous':        modules.postMsg(consts.MSG_CMD_PREVIOUS)
        elif action in ['Play', 'Pause']: modules.postMsg(consts.MSG_CMD_TOGGLE_PAUSE)


    # --== Message handlers ==--


    def onAppStarted(self):
        """ The application has started """
        # Try first with the new interface (Gnome >= 2.2)
        try:
            service = dbus.SessionBus().get_object('org.gnome.SettingsDaemon', '/org/gnome/SettingsDaemon/MediaKeys')
            self.dbusInterface = dbus.Interface(service, 'org.gnome.SettingsDaemon.MediaKeys')
            self.dbusInterface.GrabMediaPlayerKeys(APP_UID, time())
            self.dbusInterface.connect_to_signal('MediaPlayerKeyPressed', self.onMediaKey)
        except:
            # If it didn't work, try the old way
            print traceback.format_exc()
            try:
                service = dbus.SessionBus().get_object('org.gnome.SettingsDaemon', '/org/gnome/SettingsDaemon')
                self.dbusInterface = dbus.Interface(service, 'org.gnome.SettingsDaemon')
                self.dbusInterface.GrabMediaPlayerKeys(APP_UID, time())
                self.dbusInterface.connect_to_signal('MediaPlayerKeyPressed', self.onMediaKey)
            except:
                log.logger.error('[%s] Error while initializing\n\n%s' % (MOD_INFO[modules.MODINFO_NAME], traceback.format_exc()))
                self.dbusInterface = None


    def onAppQuit(self):
        """ The application is about to terminate """
        if self.dbusInterface is not None:
            self.dbusInterface.ReleaseMediaPlayerKeys(APP_UID)
