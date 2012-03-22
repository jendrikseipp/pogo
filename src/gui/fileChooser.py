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


def openFile(parent, title):
    """ Return the selected file, or None if cancelled """
    global __currDir

    btn    = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
    dialog = gtk.FileChooserDialog(title, parent, gtk.FILE_CHOOSER_ACTION_OPEN, btn)

    dialog.set_select_multiple(False)
    dialog.set_current_folder(__currDir)

    file = None
    if dialog.run() == gtk.RESPONSE_OK:
        file = dialog.get_filename()

    __currDir = dialog.get_current_folder()
    dialog.destroy()

    return file


def openDirectory(parent, title):
    """ Return a directory, or None if cancelled """
    global __currDir

    btn    = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
    dialog = gtk.FileChooserDialog(title, parent, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, btn)

    dialog.set_select_multiple(False)
    dialog.set_current_folder(__currDir)

    directory = None
    if dialog.run() == gtk.RESPONSE_OK:
        directory = dialog.get_filename()

    __currDir = dialog.get_current_folder()
    dialog.destroy()

    return directory


def save(parent, title, defaultFile, defaultDir=None):
    """ Return a filename, or None if cancelled """
    global __currDir

    btn    = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK)
    dialog = gtk.FileChooserDialog(title, parent, gtk.FILE_CHOOSER_ACTION_SAVE, btn)

    dialog.set_current_name(defaultFile)
    dialog.set_do_overwrite_confirmation(True)

    if defaultDir is None: dialog.set_current_folder(__currDir)
    else:                  dialog.set_current_folder(defaultDir)

    file = None
    if dialog.run() == gtk.RESPONSE_OK:
        file = dialog.get_filename()

    __currDir = dialog.get_current_folder()
    dialog.destroy()

    return file
