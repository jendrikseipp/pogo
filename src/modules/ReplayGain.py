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

import modules

from tools   import consts
from gettext import gettext as _


MOD_INFO = ('ReplayGain', _('ReplayGain'), _('Normalize volume'), [], False, False)


class ReplayGain(modules.Module):
    """ This module enables the GStreamer ReplayGain element """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_MOD_LOADED:   self.onRestartRequired,
                        consts.MSG_EVT_APP_STARTED:  self.onAppStarted,
                        consts.MSG_EVT_MOD_UNLOADED: self.onRestartRequired,
                   }

        modules.Module.__init__(self, handlers)


    # --== Message handlers ==--


    def onAppStarted(self):
        """ The application has just been started """
        modules.postMsg(consts.MSG_CMD_ENABLE_RG)


    def onRestartRequired(self):
        """ A restart of the application is required """
        self.restartRequired()
