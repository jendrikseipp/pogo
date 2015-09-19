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

import gtk, tools


__currDir = tools.consts.dirBaseUsr


def _open(parent, title, action):
    """ Return a directory, or None if cancelled """
    global __currDir

    btn = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
    dialog = Gtk.FileChooserDialog(title, parent, action, btn)

    dialog.set_select_multiple(False)
    dialog.set_current_folder(__currDir)

    path = None
    if dialog.run() == Gtk.ResponseType.OK:
        path = dialog.get_filename()

    __currDir = dialog.get_current_folder()
    dialog.destroy()
    return path


def openFile(parent, title):
    """ Return the selected file, or None if cancelled """
    return _open(parent, title, Gtk.FileChooserAction.OPEN)


def openDirectory(parent, title):
    """ Return a directory, or None if cancelled """
    return _open(parent, title, Gtk.FileChooserAction.SELECT_FOLDER)


def save(parent, title, defaultFile, defaultDir=None):
    """ Return a filename, or None if cancelled """
    global __currDir

    btn    = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
    dialog = Gtk.FileChooserDialog(title, parent, Gtk.FileChooserAction.SAVE, btn)

    dialog.set_current_name(defaultFile)
    dialog.set_do_overwrite_confirmation(True)

    if defaultDir is None: dialog.set_current_folder(__currDir)
    else:                  dialog.set_current_folder(defaultDir)

    file = None
    if dialog.run() == Gtk.ResponseType.OK:
        file = dialog.get_filename()

    __currDir = dialog.get_current_folder()
    dialog.destroy()

    return file
