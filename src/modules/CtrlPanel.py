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

import modules
from tools import consts, prefs, sec2str


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


    def set_time(self, seconds):
        if seconds > self.currTrackLength:
            seconds = self.currTrackLength

        elapsed = sec2str(seconds)
        total = sec2str(self.currTrackLength)
        self.sclSeek.set_tooltip_text('%s / %s' % (elapsed, total))


    def set_tooltips(self, uimanager):
        '''
        Little work-around:
        Tooltips are not shown for menuitems that have been created with uimanager.
        We have to do it manually.

        Icons will not show up in recent GNOME versions, this is not a bug.
        '''
        groups = uimanager.get_action_groups()
        for group in groups:
            actions = group.list_actions()
            for action in actions:
                widgets = action.get_proxies()
                tooltip = action.get_property('tooltip')
                if tooltip:
                    for widget in widgets:
                        widget.set_tooltip_markup(tooltip)


   # --== Message handler ==--


    def onAppStarted(self):
        """ Real initialization function, called when this module has been loaded """
        self.currTrackLength = 0
        self.sclBeingDragged = False

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

        self.uimanager = Gtk.UIManager()
        self.main_window = wTree.get_object('win-main')

        menu_xml = '''
        <ui>
        <popup name="ButtonMenu">
            <menuitem action="Options"/>
            <menuitem action="About"/>
        </popup>
        </ui>'''

        # Create an ActionGroup
        actiongroup = Gtk.ActionGroup('MainActionGroup')

        # Create actions
        actiongroup.add_actions([
            ('ButtonMenu', None, None),
            #('Quit', Gtk.STOCK_QUIT, None, None, None,
            #    lambda widget: self.onDelete(self.main_window, None)),
            ('Options', Gtk.STOCK_PREFERENCES, None,
                '<Ctrl>p', None, lambda item: modules.showPreferences()),
            #('Help', Gtk.STOCK_HELP, None,
            #    '<Ctrl>h', None, self.on_help_menu_item_activate),
            ('About', Gtk.STOCK_ABOUT, None,
                None, None, self.onAbout),
            ])

        # Add the actiongroup to the uimanager
        self.uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
        self.uimanager.add_ui_from_string(menu_xml)

        # Create a Menu
        button_menu = self.uimanager.get_widget('/ButtonMenu')

        menu_button = Gtk.MenuToolButton(None, None)
        hbox = menu_button.get_child()
        button, toggle_button = hbox.get_children()
        hbox.remove(button)

        img = Gtk.Image.new_from_stock(Gtk.STOCK_PREFERENCES,
                                       Gtk.IconSize.SMALL_TOOLBAR)

        arrow = toggle_button.get_child()
        toggle_button.remove(arrow)
        hbox = Gtk.HBox()
        hbox.add(img)
        toggle_button.add(hbox)
        menu_button.show()


        toolbar_hbox = wTree.get_object('hbox4')
        toolbar_hbox.pack_end(menu_button, False, False, 0)
        # Move it to the right
        toolbar_hbox.reorder_child(menu_button, 0)
        menu_button.set_menu(button_menu)

        self.set_tooltips(self.uimanager)
        accelgroup = self.uimanager.get_accel_group()
        self.main_window.add_accel_group(accelgroup)


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
        if not self.sclBeingDragged:
            self.set_time(seconds)

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
        self.sclBeingDragged = True
        self.set_time(int(value))


    def onSeekValueChanged(self, range):
        """ The user has moved the seek slider """
        modules.postMsg(consts.MSG_CMD_SEEK, {'seconds': int(range.get_value())})
        self.sclBeingDragged = False


    def onAbout(self, item):
        """ Show the about dialog box """
        import gui.about
        gui.about.show(self.main_window)


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
