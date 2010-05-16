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

import gtk, tools


def __msgBox(parent, type, buttons, header, text):
    """ Show a generic message box """
    dlg = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, type, buttons, header)
    dlg.set_title(tools.consts.appName)

    if text is None: dlg.set_markup(header)
    else:            dlg.format_secondary_markup(text)

    response = dlg.run()
    dlg.destroy()
    return response


# Functions used to display various message boxes
def infoMsgBox(    parent, header, text=None):        __msgBox(parent, gtk.MESSAGE_INFO,     gtk.BUTTONS_OK,     header, text)
def errorMsgBox(   parent, header, text=None):        __msgBox(parent, gtk.MESSAGE_ERROR,    gtk.BUTTONS_OK,     header, text)
def questionMsgBox(parent, header, text=None): return __msgBox(parent, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, header, text)
