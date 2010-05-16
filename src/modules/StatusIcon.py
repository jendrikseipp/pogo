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

import gtk, modules, os.path

from tools   import consts, loadGladeFile, prefs
from gettext import gettext as _

MOD_INFO = ('Status Icon', _('Status Icon'), _('Add an icon to the notification area'), [], False, False)


class StatusIcon(modules.Module):

    def __init__(self):
        """ Constructor """
        modules.Module.__init__(self, (consts.MSG_EVT_MOD_LOADED, consts.MSG_EVT_MOD_UNLOADED,  consts.MSG_EVT_APP_STARTED,
                                       consts.MSG_EVT_NEW_TRACK,  consts.MSG_EVT_PAUSED,        consts.MSG_EVT_UNPAUSED,
                                       consts.MSG_EVT_STOPPED,    consts.MSG_EVT_NEW_TRACKLIST, consts.MSG_EVT_TRACK_MOVED))


    def install(self):
        """ Install the Status icon """
        self.tooltip          = consts.appName
        self.isPaused         = False
        self.popupMenu        = None
        self.isPlaying        = False
        self.icoNormal        = None
        self.mainWindow       = prefs.getWidgetsTree().get_widget('win-main')
        self.trackHasNext     = False
        self.trackHasPrev     = False
        self.emptyTracklist   = True
        self.isMainWinVisible = True
        # The status icon does not support RGBA, so make sure to use the RGB color map when creating it
        colormap = self.mainWindow.get_screen().get_rgb_colormap()
        gtk.widget_push_colormap(self.mainWindow.get_screen().get_rgb_colormap())
        self.statusIcon = gtk.StatusIcon()
        gtk.widget_pop_colormap()
        # GTK+ handlers
        self.statusIcon.connect('activate',     self.toggleWinVisibility)
        self.statusIcon.connect('popup-menu',   self.onPopupMenu)
        self.statusIcon.connect('size-changed', self.renderIcons)
        # Install everything
        self.statusIcon.set_tooltip(consts.appName)
        self.onNewTrack(None)
        self.statusIcon.set_visible(True)


    def uninstall(self):
        """ Uninstall the Status icon """
        self.statusIcon.set_visible(False)
        self.statusIcon = None
        if not self.isMainWinVisible:
            self.mainWindow.show()
            self.isMainWinVisible = True


    def renderIcons(self, statusIcon, availableSize):
        """ (Re) Create icons based the available tray size """
        # Normal icon
        if   availableSize >= 48+2: self.icoNormal = gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon48)
        elif availableSize >= 32+2: self.icoNormal = gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon32)
        elif availableSize >= 24+2: self.icoNormal = gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon24)
        else:                       self.icoNormal = gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon16)

        # Paused icon
        self.icoPause = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, self.icoNormal.get_width(), self.icoNormal.get_height())
        self.icoPause.fill(0x00000000)
        self.icoNormal.composite(self.icoPause, 0, 0, self.icoNormal.get_width(), self.icoNormal.get_height(), 0, 0, 1, 1, gtk.gdk.INTERP_HYPER, 100)

        if self.icoNormal.get_width() == 16: pauseStock = self.mainWindow.render_icon(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_MENU)
        else:                                pauseStock = self.mainWindow.render_icon(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)

        diffX = self.icoPause.get_width() - pauseStock.get_width()
        diffY = self.icoPause.get_height() - pauseStock.get_height()
        pauseStock.composite(self.icoPause, 0, 0, pauseStock.get_width(), pauseStock.get_height(), diffX/2, diffY/2, 1, 1, gtk.gdk.INTERP_HYPER, 255)

        # Use the correct icon
        if self.isPaused: statusIcon.set_from_pixbuf(self.icoPause)
        else:             statusIcon.set_from_pixbuf(self.icoNormal)


    def onNewTrack(self, track):
        """ A new track is being played, None if none """
        if track is None: self.tooltip = consts.appName
        else:             self.tooltip  = '%s - %s' % (track.getArtist(), track.getTitle())

        self.isPaused  = False
        self.isPlaying = track is not None

        self.statusIcon.set_from_pixbuf(self.icoNormal)
        self.statusIcon.set_tooltip(self.tooltip)


    def onPause(self):
        """ The current track has been paused """
        self.isPaused = True
        self.statusIcon.set_from_pixbuf(self.icoPause)
        self.statusIcon.set_tooltip(_('%(tooltip)s [paused]') % {'tooltip': self.tooltip})


    def onUnpause(self):
        """ The current track has been unpaused """
        self.isPaused = False
        self.statusIcon.set_from_pixbuf(self.icoNormal)
        self.statusIcon.set_tooltip(self.tooltip)


    def toggleWinVisibility(self, statusIcon):
        """ Show/hide the main window """
        if not self.isMainWinVisible:
            self.mainWindow.show()
            self.isMainWinVisible = True
        elif self.mainWindow.has_toplevel_focus():
            self.mainWindow.hide()
            self.isMainWinVisible = False
        else:
            self.mainWindow.hide()
            self.mainWindow.show()


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ Handle messages sent to this module """
        if   msg == consts.MSG_EVT_PAUSED:        self.onPause()
        elif msg == consts.MSG_EVT_STOPPED:       self.onNewTrack(None)
        elif msg == consts.MSG_EVT_UNPAUSED:      self.onUnpause()
        elif msg == consts.MSG_EVT_NEW_TRACK:     self.onNewTrack(params['track'])
        elif msg == consts.MSG_EVT_MOD_LOADED:    self.install()
        elif msg == consts.MSG_EVT_TRACK_MOVED:   self.trackHasNext, self.trackHasPrev = params['hasNext'], params['hasPrevious']
        elif msg == consts.MSG_EVT_APP_STARTED:   self.install()
        elif msg == consts.MSG_EVT_MOD_UNLOADED:  self.uninstall()
        elif msg == consts.MSG_EVT_NEW_TRACKLIST: self.emptyTracklist = (len(params['tracks']) == 0)


    # --== GTK handlers ==--


    def onPopupMenu(self, statusIcon, button, time):
        """ The user asks for the popup menu """
        if self.popupMenu is None:
            wTree              = loadGladeFile('StatusIconMenu.glade')
            self.menuPlay      = wTree.get_widget('item-play')
            self.menuStop      = wTree.get_widget('item-stop')
            self.menuNext      = wTree.get_widget('item-next')
            self.popupMenu     = wTree.get_widget('menu-popup')
            self.menuPause     = wTree.get_widget('item-pause')
            self.menuPrevious  = wTree.get_widget('item-previous')
            self.menuSeparator = wTree.get_widget('item-separator')
            # Connect handlers
            wTree.get_widget('item-quit').connect('activate', lambda btn: modules.postQuitMsg())
            wTree.get_widget('item-preferences').connect('activate', lambda btn: modules.showPreferences())
            self.menuPlay.connect('activate',     lambda btn: modules.postMsg(consts.MSG_CMD_TOGGLE_PAUSE))
            self.menuStop.connect('activate',     lambda btn: modules.postMsg(consts.MSG_CMD_STOP))
            self.menuNext.connect('activate',     lambda btn: modules.postMsg(consts.MSG_CMD_NEXT))
            self.menuPrevious.connect('activate', lambda btn: modules.postMsg(consts.MSG_CMD_PREVIOUS))
            self.menuPause.connect('activate',    lambda btn: modules.postMsg(consts.MSG_CMD_TOGGLE_PAUSE))
            self.popupMenu.show_all()

        # Enable only relevant menu entries
        self.menuStop.set_sensitive(self.isPlaying)
        self.menuNext.set_sensitive(self.isPlaying and self.trackHasNext)
        self.menuPause.set_sensitive(self.isPlaying and not self.isPaused)
        self.menuPrevious.set_sensitive(self.isPlaying and self.trackHasPrev)
        self.menuPlay.set_sensitive((not (self.isPlaying or self.emptyTracklist)) or self.isPaused)

        self.popupMenu.popup(None, None, gtk.status_icon_position_menu, button, time, statusIcon)
