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

import dbus, optparse, sys

from tools import consts


# Command line
optparser = optparse.OptionParser(usage='Usage: %prog [options] [FILE(s)]')
optparser.add_option('-p', '--playbin', action='store_true', default=False, help='use the playbin GStreamer component instead of playbin2')
optparser.add_option('--no-glossy-cover', action='store_true', default=False, help='disable the gloss effect applied to covers')
optparser.add_option('--multiple-instances', action='store_true', default=False, help='start a new instance even if one is already running')

(optOptions, optArgs) = optparser.parse_args()


# Check whether DAP is already running?
if not optOptions.multiple_instances:
    shouldStop  = False
    dbusSession = None

    try:
        dbusSession    = dbus.SessionBus()
        activeServices = dbusSession.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus').ListNames()

        if consts.dbusService in activeServices:
            shouldStop      = True
            remoteObject    = dbusSession.get_object(consts.dbusService, '/TrackList')
            remoteInterface = dbus.Interface(remoteObject, consts.dbusInterface)

            # Fill the current instance with the given tracks, if any
            if len(optArgs) != 0:
                remoteInterface.Clear()
                remoteInterface.AddTracks(optArgs, True)
    except:
        pass

    if dbusSession is not None:
        dbusSession.close()

    if shouldStop:
        sys.exit(1)


# Start a new instance
import gettext, gobject, gtk, locale, signal

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
    import atexit, dbus.mainloop.glib, modules


    def onDelete(win, event):
        """ Use our own quit sequence, that will itself destroy the window """
        window.hide()
        modules.postQuitMsg()
        return True


    def onResize(win, rect):
        """ Save the new size of the window """
        if win.window is not None and not win.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED:
            prefs.set(__name__, 'win-width',  rect.width)
            prefs.set(__name__, 'win-height', rect.height)

            if prefs.get(__name__, 'view-mode', DEFAULT_VIEW_MODE)in (consts.VIEW_MODE_FULL, consts.VIEW_MODE_PLAYLIST):
                prefs.set(__name__, 'full-win-height', rect.height)


    def onAbout(item):
        """ Show the about dialog box """
        import gui.about
        gui.about.show(window)


    def onHelp(item):
        """ Show help page in the web browser """
        import webbrowser
        webbrowser.open(consts.urlHelp)


    def onState(win, evt):
        """ Save the new state of the window """
        prefs.set(__name__, 'win-is-maximized', bool(evt.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED))


    def atExit():
        """ Final function, called just before exiting the Python interpreter """
        prefs.save()
        log.logger.info('Stopped')


    # D-Bus
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # Make sure to perform a few actions before exiting the Python interpreter
    atexit.register(atExit)
    signal.signal(signal.SIGTERM, lambda sig, frame: onDelete(window, None))

    # GTK handlers
    window.connect('delete-event', onDelete)
    window.connect('size-allocate', onResize)
    window.connect('window-state-event', onState)
    paned.connect('size-allocate', lambda win, rect: prefs.set(__name__, 'paned-pos', paned.get_position()))
    wTree.get_widget('menu-mode-mini').connect('activate', onViewMode, consts.VIEW_MODE_MINI)
    wTree.get_widget('menu-mode-full').connect('activate', onViewMode, consts.VIEW_MODE_FULL)
    wTree.get_widget('menu-mode-playlist').connect('activate', onViewMode, consts.VIEW_MODE_PLAYLIST)
    wTree.get_widget('menu-quit').connect('activate', lambda item: onDelete(window, None))
    wTree.get_widget('menu-about').connect('activate', onAbout)
    wTree.get_widget('menu-help').connect('activate', onHelp)
    wTree.get_widget('menu-preferences').connect('activate', lambda item: modules.showPreferences())

    # Let's go
    modules.postMsg(consts.MSG_EVT_APP_STARTED)


def onViewMode(item, mode):
    """ Wrapper for setViewMode(): Don't do anything if the mode the same as the current one """
    if item.get_active() and mode != prefs.get(__name__, 'view-mode', DEFAULT_VIEW_MODE):
        setViewMode(mode, True)


def setViewMode(mode, resize):
    """ Change the view mode to the given one """
    lastMode = prefs.get(__name__, 'view-mode', DEFAULT_VIEW_MODE)
    prefs.set(__name__, 'view-mode', mode)

    (winWidth, winHeight) = window.get_size()

    if mode == consts.VIEW_MODE_FULL:
        paned.get_child1().show()
        wTree.get_widget('statusbar').show()
        wTree.get_widget('box-btn-tracklist').show()
        wTree.get_widget('scrolled-tracklist').show()
        wTree.get_widget('box-trkinfo').show()
        if resize:
            if lastMode != consts.VIEW_MODE_FULL: winWidth  = winWidth + paned.get_position()
            if lastMode == consts.VIEW_MODE_MINI: winHeight = prefs.get(__name__, 'full-win-height', DEFAULT_WIN_HEIGHT)

            window.resize(winWidth, winHeight)
        return

    paned.get_child1().hide()
    if resize and lastMode == consts.VIEW_MODE_FULL:
        winWidth = winWidth - paned.get_position()
        window.resize(winWidth, winHeight)

    if mode == consts.VIEW_MODE_PLAYLIST:
        wTree.get_widget('statusbar').show()
        wTree.get_widget('box-btn-tracklist').hide()
        wTree.get_widget('scrolled-tracklist').show()
        wTree.get_widget('box-trkinfo').show()
        if resize and lastMode == consts.VIEW_MODE_MINI:
            window.resize(winWidth, prefs.get(__name__, 'full-win-height', DEFAULT_WIN_HEIGHT))
        return

    wTree.get_widget('statusbar').hide()
    wTree.get_widget('box-btn-tracklist').hide()
    wTree.get_widget('scrolled-tracklist').hide()

    if mode == consts.VIEW_MODE_MINI: wTree.get_widget('box-trkinfo').show()
    else:                             wTree.get_widget('box-trkinfo').hide()

    if resize: window.resize(winWidth, 1)


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

# Restore last view mode
viewMode = prefs.get(__name__, 'view-mode', DEFAULT_VIEW_MODE)

if viewMode == consts.VIEW_MODE_FULL:
    wTree.get_widget('menu-mode-full').set_active(True)
else:
    if viewMode == consts.VIEW_MODE_MINI: wTree.get_widget('menu-mode-mini').set_active(True)
    else:                                 wTree.get_widget('menu-mode-playlist').set_active(True)

    setViewMode(viewMode, False)

# Restore sizes once more
window.resize(prefs.get(__name__, 'win-width', DEFAULT_WIN_WIDTH), prefs.get(__name__, 'win-height', DEFAULT_WIN_HEIGHT))
paned.set_position(prefs.get(__name__, 'paned-pos', DEFAULT_PANED_POS))

# Initialization done, let's continue the show
gobject.idle_add(realStartup)
gtk.main()
