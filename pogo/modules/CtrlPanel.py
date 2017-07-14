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

from gettext import gettext as _

from gi.repository import Gtk

from pogo import modules
from pogo.tools import consts, prefs, sec2str


MOD_INFO = ('Control Panel', 'Control Panel', '', [], True, False)

PLAY_PAUSE_ICON_SIZE = Gtk.IconSize.LARGE_TOOLBAR


class CtrlPanel(modules.Module):
    """ This module manages the control panel with the buttons and the slider """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_PAUSED:           self.onPaused,
                        consts.MSG_EVT_STOPPED:          self.onStopped,
                        consts.MSG_EVT_UNPAUSED:         self.onUnpaused,
                        consts.MSG_EVT_NEW_TRACK:        self.onNewTrack,
                        consts.MSG_EVT_TRACK_MOVED:      self.onCurrentTrackMoved,
                        consts.MSG_EVT_APP_STARTED:      self.onAppStarted,
                        consts.MSG_EVT_NEW_TRACKLIST:    self.onNewTracklist,
                        consts.MSG_EVT_TRACK_POSITION:   self.onNewTrackPosition,
                   }

        modules.Module.__init__(self, handlers)


    def set_time_tooltip(self, seconds):
        if seconds > self.currTrackLength:
            seconds = self.currTrackLength

        elapsed = sec2str(seconds)
        total = sec2str(self.currTrackLength)
        self.sclSeek.set_tooltip_text('%s / %s' % (elapsed, total))


   # --== Message handler ==--


    def onAppStarted(self):
        """ Real initialization function, called when this module has been loaded """
        self.currTrackLength = 0

        # Widgets
        wTree             = prefs.getWidgetsTree()
        self.btnPlay      = wTree.get_object('btn-play')
        self.btnNext      = wTree.get_object('btn-next')
        self.btnPrev      = wTree.get_object('btn-previous')
        self.sclSeek      = wTree.get_object('scl-position')

        # GTK handlers
        self.btnNext.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_NEXT))
        self.btnPrev.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_PREVIOUS))
        self.btnPlay.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_TOGGLE_PAUSE))
        self.sclSeek.connect('change-value', self.onSeekChangingValue)
        self.sclSeek.connect('value-changed', self.onSeekValueChanged)

        self.sclSeek.hide()

        # Add preferences button.
        preferences_img = Gtk.Image.new_from_icon_name(
            'preferences-system', Gtk.IconSize.SMALL_TOOLBAR)
        preferences_button = Gtk.ToolButton.new(preferences_img, None)
        toolbar_hbox = wTree.get_object('hbox4')
        toolbar_hbox.pack_end(preferences_button, False, False, 0)
        # Move button to the right.
        toolbar_hbox.reorder_child(preferences_button, 0)
        preferences_button.connect('clicked', lambda item: modules.showPreferences())
        preferences_button.show_all()


    def onNewTrack(self, track):
        """ A new track is being played """
        self.btnPlay.set_sensitive(True)
        self.btnPlay.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_MEDIA_PAUSE, PLAY_PAUSE_ICON_SIZE))
        self.btnPlay.set_tooltip_text(_('Pause the current track'))

        self.currTrackLength = track.getLength()
        self.sclSeek.show()
        self.onNewTrackPosition(0)

        # Must be done last
        if self.currTrackLength != 0:
            self.sclSeek.set_range(0, self.currTrackLength)


    def onStopped(self):
        """ The playback has been stopped """
        self.btnNext.set_sensitive(False)
        self.btnPrev.set_sensitive(False)
        self.btnPlay.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_MEDIA_PLAY, PLAY_PAUSE_ICON_SIZE))
        self.btnPlay.set_tooltip_text(_('Play the first selected track of the playlist'))
        self.sclSeek.hide()


    def onNewTrackPosition(self, seconds):
        """ The track position has changed """
        self.set_time_tooltip(seconds)

        # Make sure the handler will not be called
        self.sclSeek.handler_block_by_func(self.onSeekValueChanged)
        self.sclSeek.set_value(seconds)
        self.sclSeek.handler_unblock_by_func(self.onSeekValueChanged)


    def onCurrentTrackMoved(self, hasPrevious, hasNext):
        """ Update previous and next buttons """
        self.btnNext.set_sensitive(hasNext)
        self.btnPrev.set_sensitive(hasPrevious)


    def onPaused(self):
        """ The playback has been paused """
        self.btnPlay.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_MEDIA_PLAY, PLAY_PAUSE_ICON_SIZE))
        self.btnPlay.set_tooltip_text(_('Continue playing the current track'))


    def onUnpaused(self):
        """ The playback has been unpaused """
        self.btnPlay.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_MEDIA_PAUSE, PLAY_PAUSE_ICON_SIZE))
        self.btnPlay.set_tooltip_text(_('Pause the current track'))


    def onNewTracklist(self, tracks, playtime):
        """ A new tracklist has been set """
        self.btnPlay.set_sensitive(playtime != 0)


    # --== GTK handlers ==--

    def onSeekChangingValue(self, range, scroll, value):
        """ The user is moving the seek slider """
        self.set_time_tooltip(int(value))


    def onSeekValueChanged(self, range):
        """ The user has moved the seek slider """
        modules.postMsg(consts.MSG_CMD_SEEK, {'seconds': int(range.get_value())})


    def onHelp(self, item):
        """ Show help page in the web browser """
        import webbrowser
        webbrowser.open(consts.urlHelp)


    def onDelete(self, win, event):
        """ Use our own quit sequence, that will itself destroy the window """
        ##window.hide()
        win.hide()
        modules.postQuitMsg()
        return True
