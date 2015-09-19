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

from gi.repository import GdkPixbuf
from gi.repository import Gtk


__lbl               = None
__dirMenuIcon       = None
__prefsBtnIcon      = None
__nullMenuIcon      = None
__playMenuIcon      = None
__pauseMenuIcon     = None
__cdromMenuIcon     = None
__errorMenuIcon     = None
__infoMenuIcon      = None
__mediaDirMenuIcon  = None
__mediaFileMenuIcon = None


def __render(stock, size):
    """ Return the given stock icon rendered at the given size """
    global __lbl

    if __lbl is None:
        __lbl = Gtk.Label()

    return __lbl.render_icon(stock, size)


def dirMenuIcon():
    """ Directories """
    global __dirMenuIcon

    if __dirMenuIcon is None:
        __dirMenuIcon = __render(Gtk.STOCK_DIRECTORY, Gtk.IconSize.MENU)

    return __dirMenuIcon


def prefsBtnIcon():
    """ Preferences """
    global __prefsBtnIcon

    if __prefsBtnIcon is None:
        __prefsBtnIcon = __render(Gtk.STOCK_PREFERENCES, Gtk.IconSize.BUTTON)

    return __prefsBtnIcon


def playMenuIcon():
    """ Play """
    global __playMenuIcon

    if __playMenuIcon is None:
        __playMenuIcon = __render(Gtk.STOCK_MEDIA_PLAY, Gtk.IconSize.MENU)

    return __playMenuIcon


def pauseMenuIcon():
    """ Pause """
    global __pauseMenuIcon

    if __pauseMenuIcon is None:
        __pauseMenuIcon = __render(Gtk.STOCK_MEDIA_PAUSE, Gtk.IconSize.MENU)

    return __pauseMenuIcon


def cdromMenuIcon():
    """ CD-ROM """
    global __cdromMenuIcon

    if __cdromMenuIcon is None:
        __cdromMenuIcon = __render(Gtk.STOCK_CDROM, Gtk.IconSize.MENU)

    return __cdromMenuIcon


def errorMenuIcon():
    """ Error """
    global __errorMenuIcon

    if __errorMenuIcon is None:
        __errorMenuIcon = __render(Gtk.STOCK_CANCEL, Gtk.IconSize.MENU)

    return __errorMenuIcon


def infoMenuIcon():
    """ Error """
    global __infoMenuIcon

    if __infoMenuIcon is None:
        __infoMenuIcon = __render(Gtk.STOCK_INFO, Gtk.IconSize.MENU)

    return __infoMenuIcon


def nullMenuIcon():
    """ Transparent icon """
    global __nullMenuIcon

    if __nullMenuIcon is None:
        __nullMenuIcon = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 16, 16)
        __nullMenuIcon.fill(0x00000000)

    return __nullMenuIcon


def mediaDirMenuIcon():
    """ Media directory """
    global __mediaDirMenuIcon

    if __mediaDirMenuIcon is None:
        __mediaDirMenuIcon = dirMenuIcon().copy()  # We need a copy to modify it
        cdromMenuIcon().composite(__mediaDirMenuIcon, 5, 5, 11, 11, 5, 5, 0.6875, 0.6875, GdkPixbuf.InterpType.HYPER, 255)

    return __mediaDirMenuIcon


def mediaFileMenuIcon():
    """ Media file """
    global __mediaFileMenuIcon

    if __mediaFileMenuIcon is None:
        __mediaFileMenuIcon = __render(Gtk.STOCK_FILE, Gtk.IconSize.MENU).copy()  # We need a copy to modify it
        cdromMenuIcon().composite(__mediaFileMenuIcon, 5, 5, 11, 11, 5, 5, 0.6875, 0.6875, GdkPixbuf.InterpType.HYPER, 255)

    return __mediaFileMenuIcon
