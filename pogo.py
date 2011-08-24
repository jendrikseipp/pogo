#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007  François Ingelrest (Francois.Ingelrest@gmail.com)
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

import optparse
import os
import sys

prefix = '/usr'
installed_src_dir = os.path.join(prefix, 'share/pogo/src')
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')

if os.path.exists(src_dir):
    print 'Running from tarball or bzr branch'
    sys.path.insert(0, src_dir)
elif os.path.exists(installed_src_dir):
    print 'Running deb package or "make installation"'
    sys.path.insert(0, installed_src_dir)
else:
    sys.exit('Source files could not be found')


from tools import consts


# Command line
optparser = optparse.OptionParser(usage='Usage: %prog [options] [FILE(s)]')
optparser.add_option('--playbin', action='store_true', default=False,
              help='use the playbin GStreamer component instead of playbin2')
optparser.add_option('--multiple-instances', action='store_true',
    default=False, help='start a new instance even if one is already running')

optOptions, optArgs = optparser.parse_args()


# Check whether Pogo is already running?
if not optOptions.multiple_instances:
    import dbus

    shouldStop = False
    dbusSession = None

    try:
        dbusSession = dbus.SessionBus()
        activeServices = dbusSession.get_object('org.freedesktop.DBus',
                                        '/org/freedesktop/DBus').ListNames()

        if consts.dbusService in activeServices:
            shouldStop = True

            # Raise the window of the already running instance
            dbus.Interface(dbusSession.get_object(consts.dbusService, '/'),
                           consts.dbusInterface).RaiseWindow()

            # Fill the current instance with the given tracks, if any
            if len(optArgs) != 0:
                # make the paths absolute
                paths = map(os.path.abspath, optArgs)
                print 'Appending to the playlist:'
                print '\n'.join(paths)
                dbus.Interface(dbusSession.get_object(consts.dbusService,
                '/TrackList'), consts.dbusInterface).AddTracks(paths, True)
    except:
        pass

    if dbusSession is not None:
        dbusSession.close()

    if shouldStop:
        import sys
        print 'There is already one Pogo instance running. Exiting.'
        sys.exit(1)


# Start a new instance
import gettext
import locale

import gobject
import gtk

from tools import loadGladeFile, log, prefs

DEFAULT_VIEW_MODE = consts.VIEW_MODE_FULL
DEFAULT_PANED_POS = 370  # 300
DEFAULT_WIN_WIDTH = 900  # 750
DEFAULT_WIN_HEIGHT = 500  # 470
DEFAULT_MAXIMIZED_STATE = False


def realStartup(window, paned):
    """
    Perform all the initialization stuff which is not mandatory to display the
    window. This function should be called within the GTK main loop, once the
    window has been displayed
    """

    # Is the application started for the first time?
    first_start = prefs.get(__name__, 'first-time', True)
    print 'First start:', first_start
    if first_start:
        prefs.set(__name__, 'first-time', False)

        # Enable some modules by default
        prefs.set('modules', 'enabled_modules', ['Covers', 'Desktop Notification'])

    import atexit
    import signal
    import dbus.mainloop.glib
    import modules

    def onDelete(win, event):
        """ Use our own quit sequence, that will itself destroy the window """
        win.hide()
        modules.postQuitMsg()
        return True

    def onResize(win, rect):
        """ Save the new size of the window """
        maximized = win.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED
        if win.window is not None and not maximized:
            prefs.set(__name__, 'win-width',  rect.width)
            prefs.set(__name__, 'win-height', rect.height)

            view_mode = prefs.get(__name__, 'view-mode', DEFAULT_VIEW_MODE)
            if view_mode in (consts.VIEW_MODE_FULL, consts.VIEW_MODE_PLAYLIST):
                prefs.set(__name__, 'full-win-height', rect.height)

    def onPanedResize(win, rect):
        prefs.set(__name__, 'paned-pos', paned.get_position())

    def onState(win, event):
        """ Save the new state of the window """
        if event.changed_mask & gtk.gdk.WINDOW_STATE_MAXIMIZED:
            maximized = bool(event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED)
            prefs.set(__name__, 'win-is-maximized', maximized)

    def atExit():
        """
        Final function, called just before exiting the Python interpreter
        """
        prefs.save()
        log.logger.info('Stopped')

    # D-Bus
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # Register some handlers (Signal SIGKILL cannot be caught)
    atexit.register(atExit)
    signal.signal(signal.SIGINT,  lambda sig, frame: onDelete(window, None))
    signal.signal(signal.SIGTERM, lambda sig, frame: onDelete(window, None))

    # GTK handlers
    window.connect('delete-event', onDelete)
    window.connect('size-allocate', onResize)
    window.connect('window-state-event', onState)
    paned.connect('size-allocate', onPanedResize)

    # Let's go
    gobject.idle_add(modules.postMsg, consts.MSG_EVT_APP_STARTED)


# --== Entry point ==--

def main():
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
    gtk.window_set_default_icon_list(
                        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon16),
                        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon24),
                        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon32),
                        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon48),
                        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon64),
                        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon128))

    # Create the GUI
    wTree = loadGladeFile('MainWindow.glade')
    paned = wTree.get_widget('pan-main')
    window = wTree.get_widget('win-main')
    prefs.setWidgetsTree(wTree)

    # RGBA support
    try:
        colormap = window.get_screen().get_rgba_colormap()
        if colormap:
            gtk.widget_set_default_colormap(colormap)
    except:
        log.logger.info('No RGBA support (requires PyGTK 2.10+)')

    # Show all widgets and restore the window size BEFORE hiding some of them
    # when restoring the view mode
    # Resizing must be done before showing the window to make sure that the WM
    # correctly places the window
    if prefs.get(__name__, 'win-is-maximized', DEFAULT_MAXIMIZED_STATE):
        window.maximize()

    height = prefs.get(__name__, 'win-height', DEFAULT_WIN_HEIGHT)
    window.resize(prefs.get(__name__, 'win-width', DEFAULT_WIN_WIDTH), height)
    window.show_all()

    # Restore sizes once more
    #window.resize(prefs.get(__name__, 'win-width', DEFAULT_WIN_WIDTH), height)
    paned.set_position(prefs.get(__name__, 'paned-pos', DEFAULT_PANED_POS))

    # Initialization done, let's continue the show
    gobject.idle_add(realStartup, window, paned)
    gtk.main()

if __name__ == '__main__':
    main()
