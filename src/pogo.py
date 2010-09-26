#!/usr/bin/env python
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

import dbus, optparse

from tools import consts


# Command line
optparser = optparse.OptionParser(usage='Usage: %prog [options] [FILE(s)]')
optparser.add_option('-p', '--playbin', action='store_true', default=False, help='use the playbin GStreamer component instead of playbin2')
optparser.add_option('--no-glossy-cover', action='store_true', default=False, help='disable the gloss effect applied to covers')
optparser.add_option('--multiple-instances', action='store_true', default=False, help='start a new instance even if one is already running')

(optOptions, optArgs) = optparser.parse_args()


# Check whether Pogo is already running?
if not optOptions.multiple_instances:
    shouldStop  = False
    dbusSession = None

    try:
        dbusSession    = dbus.SessionBus()
        activeServices = dbusSession.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus').ListNames()

        if consts.dbusService in activeServices:
            ##shouldStop = True

            # Fill the current instance with the given tracks, if any
            if len(optArgs) != 0:
                dbus.Interface(dbusSession.get_object(consts.dbusService, '/TrackList'), consts.dbusInterface).SetTracks(optArgs, True)
    except:
        pass

    if dbusSession is not None:
        dbusSession.close()

    if shouldStop:
        import sys
        sys.exit(1)


# Start a new instance
import gettext, gobject, gtk, locale

from tools import loadGladeFile, log, prefs

DEFAULT_VIEW_MODE       = consts.VIEW_MODE_FULL
DEFAULT_PANED_POS       = 300
DEFAULT_WIN_WIDTH       = 750
DEFAULT_WIN_HEIGHT      = 470
DEFAULT_MAXIMIZED_STATE = False


def realStartup():
    """
        Perform all the initialization stuff which is not mandatory to display the window
        This function should be called within the GTK main loop, once the window has been displayed
    """
    import atexit, dbus.mainloop.glib, modules, signal


    def onDelete(win, event):
        """ Use our own quit sequence, that will itself destroy the window """
        ##window.hide()
        win.hide()
        modules.postQuitMsg()
        return True


    def onResize(win, rect):
        """ Save the new size of the window """
        if win.window is not None and not win.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED:
            prefs.set(__name__, 'win-width',  rect.width)
            prefs.set(__name__, 'win-height', rect.height)

            if prefs.get(__name__, 'view-mode', DEFAULT_VIEW_MODE)in (consts.VIEW_MODE_FULL, consts.VIEW_MODE_PLAYLIST):
                prefs.set(__name__, 'full-win-height', rect.height)


    def onState(win, evt):
        """ Save the new state of the window """
        prefs.set(__name__, 'win-is-maximized', bool(evt.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED))


    def atExit():
        """ Final function, called just before exiting the Python interpreter """
        prefs.save()
        log.logger.info('Stopped')


    # D-Bus
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # Register some handlers
    atexit.register(atExit)
    signal.signal(signal.SIGINT,  lambda sig, frame: onDelete(window, None))
    signal.signal(signal.SIGTERM, lambda sig, frame: onDelete(window, None))

    # GTK handlers
    window.connect('delete-event', onDelete)
    window.connect('size-allocate', onResize)
    window.connect('window-state-event', onState)
    paned.connect('size-allocate', lambda win, rect: prefs.set(__name__, 'paned-pos', paned.get_position()))

    # Let's go
    gobject.idle_add(modules.postMsg, consts.MSG_EVT_APP_STARTED)


# --== Entry point ==--


log.logger.info('Started')

# Localization
locale.setlocale(locale.LC_ALL, '')
gettext.textdomain(consts.appNameShort)
gettext.bindtextdomain(consts.appNameShort, consts.dirLocale)
gtk.glade.textdomain(consts.appNameShort)
gtk.glade.bindtextdomain(consts.appNameShort, consts.dirLocale)

# Command line
prefs.setCmdLine((optOptions, optArgs))

# PyGTK initialization
gobject.threads_init()
gtk.window_set_default_icon_list(gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon16),
                                 gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon24),
                                 gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon32),
                                 gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon48),
                                 gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon64),
                                 gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon128))

# Create the GUI
wTree  = loadGladeFile('MainWindow.glade')
paned  = wTree.get_widget('pan-main')
window = wTree.get_widget('win-main')
prefs.setWidgetsTree(wTree)

# RGBA support
try:
    colormap = window.get_screen().get_rgba_colormap()
    if colormap:
        gtk.widget_set_default_colormap(colormap)
except:
    log.logger.info('No RGBA support (requires PyGTK 2.10+)')

# Show all widgets and restore the window size BEFORE hiding some of them when restoring the view mode
# Resizing must be done before showing the window to make sure that the WM correctly places the window
if prefs.get(__name__, 'win-is-maximized', DEFAULT_MAXIMIZED_STATE):
    window.maximize()

window.resize(prefs.get(__name__, 'win-width', DEFAULT_WIN_WIDTH), prefs.get(__name__, 'win-height', DEFAULT_WIN_HEIGHT))
window.show_all()

# Restore sizes once more
window.resize(prefs.get(__name__, 'win-width', DEFAULT_WIN_WIDTH), prefs.get(__name__, 'win-height', DEFAULT_WIN_HEIGHT))
paned.set_position(prefs.get(__name__, 'paned-pos', DEFAULT_PANED_POS))

# Initialization done, let's continue the show
gobject.idle_add(realStartup)
gtk.main()
