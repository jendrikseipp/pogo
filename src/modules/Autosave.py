# -*- coding: utf-8 -*-
#
# Copyright (c) 2010  Jendrik Seipp (jendrikseipp@web.de)
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

import logging
from gettext import gettext as _

import gobject

import modules
from tools import consts

description = _('Automatically save your playlist at regular intervals')

# Module information
MOD_INFO = ('Autosave', ('Autosave'), description, [], True, False)
MOD_NAME = MOD_INFO[modules.MODINFO_NAME]



class Search(modules.ThreadedModule):

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_MOD_LOADED:          self.onModLoaded,
                        consts.MSG_EVT_MOD_UNLOADED:        self.onModUnloaded,
                   }
        modules.ThreadedModule.__init__(self, handlers)


    # --== Message handlers ==--


    def onModLoaded(self):
        """ The module has been loaded """
        # Automatically save the content after a period of time
        self.handle = gobject.timeout_add_seconds(600, self.save_to_disk)

    def onModUnloaded(self):
        # Remove the handle
