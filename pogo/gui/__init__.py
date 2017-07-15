# -*- coding: utf-8 -*-
#
# Copyright (c) 2007  François Ingelrest (Francois.Ingelrest@gmail.com)
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

from gi.repository import Gtk

from pogo import tools


def __msgBox(parent, type, buttons, header, text):
    """ Show a generic message box """
    dlg = Gtk.MessageDialog(parent, Gtk.DialogFlags.MODAL, type, buttons, header)
    dlg.set_transient_for(parent)
    dlg.set_title(tools.consts.appName)

    if text is None:
        dlg.set_markup(header)
    else:
        dlg.format_secondary_markup(text)

    response = dlg.run()
    dlg.destroy()
    return response


# Functions used to display various message boxes
def infoMsgBox(parent, header, text=None):
    __msgBox(parent, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, header, text)

def errorMsgBox(parent, header, text=None):
    __msgBox(parent, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, header, text)
