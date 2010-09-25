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

import gtk, modules

from tools   import consts, prefs, sec2str
from gettext import gettext as _

MOD_INFO = ('Control Panel', 'Control Panel', '', [], True, False)

PREFS_DEFAULT_VOLUME = 0.65

PLAY_PAUSE_ICON_SIZE = gtk.ICON_SIZE_LARGE_TOOLBAR


class CtrlPanel(modules.Module):
    """ This module manages the control panel with the buttons and the slider """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_PAUSED:           self.onPaused,
                        consts.MSG_EVT_STOPPED:          self.onStopped,
                        consts.MSG_EVT_UNPAUSED:         self.onUnpaused,
                        consts.MSG_EVT_APP_QUIT:         self.onAppQuit,
                        consts.MSG_EVT_NEW_TRACK:        self.onNewTrack,
                        consts.MSG_EVT_TRACK_MOVED:      self.onCurrentTrackMoved,
                        consts.MSG_EVT_APP_STARTED:      self.onAppStarted,
                        consts.MSG_EVT_NEW_TRACKLIST:    self.onNewTracklist,
                        consts.MSG_EVT_VOLUME_CHANGED:   self.onVolumeChanged,
                        consts.MSG_EVT_TRACK_POSITION:   self.onNewTrackPosition,
                   }

        modules.Module.__init__(self, handlers)
        
        
    def set_time(self, seconds):
        elapsed = sec2str(seconds)
        #remaining = sec2str(self.currTrackLength - seconds)
        total = sec2str(self.currTrackLength)
        ##self.lblRemaining.set_label('%s / %s' % (elapsed, total))
        self.sclSeek.set_tooltip_text(elapsed)
        
    
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
                print action.get_accel_path()
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
        ##self.btnStop      = wTree.get_widget('btn-stop')
        self.btnPlay      = wTree.get_widget('btn-play')
        self.btnNext      = wTree.get_widget('btn-next')
        self.btnPrev      = wTree.get_widget('btn-previous')
        self.sclSeek      = wTree.get_widget('scl-position')
        self.btnVolume    = wTree.get_widget('btn-volume')
        ##self.lblElapsed   = wTree.get_widget('lbl-elapsedTime')
        ##self.lblRemaining = wTree.get_widget('lbl-remainingTime')

        # Restore the volume
        volume = prefs.get(__name__, 'volume', PREFS_DEFAULT_VOLUME)
        self.btnVolume.set_value(volume)
        modules.postMsg(consts.MSG_CMD_SET_VOLUME, {'value': volume})

        # GTK handlers
        ##self.btnStop.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_STOP))
        self.btnNext.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_NEXT))
        self.btnPrev.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_PREVIOUS))
        self.btnPlay.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_TOGGLE_PAUSE))
        self.sclSeek.connect('change-value', self.onSeekChangingValue)
        self.sclSeek.connect('value-changed', self.onSeekValueChanged)
        
        ## Left mouse click jumps to current position
        self.sclSeek.connect('button-press-event', self.onSeekButtonPressed)
        self.sclSeek.connect('button-release-event', self.onSeekButtonReleased)
        
        self.btnVolume.connect('value-changed', self.onVolumeValueChanged)
        
        # Add pref button
        
        self.uimanager = gtk.UIManager()
        self.main_window = wTree.get_widget('win-main')
        
        menu_xml = '''
        <ui>
        <popup name="ButtonMenu">
            <menuitem action="Options"/>
            <menuitem action="About"/>
            <separator/>
            <menuitem action="Quit"/>
        </popup>
        </ui>'''

        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('MainActionGroup')

        # Create actions
        actiongroup.add_actions([
            ('ButtonMenu', None, None),
            ('Quit', gtk.STOCK_QUIT, None, None, None,
                lambda widget: self.onDelete(self.main_window, None)),
            ('Options', gtk.STOCK_PREFERENCES, None,
                '<Ctrl>p', None, lambda item: modules.showPreferences()),
            #('Help', gtk.STOCK_HELP, None,
            #    '<Ctrl>h', None, self.on_help_menu_item_activate),
            ('About', gtk.STOCK_ABOUT, None,
                None, None, self.onAbout),
            ])

        # Add the actiongroup to the uimanager
        self.uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
        self.uimanager.add_ui_from_string(menu_xml)

        # Create a Menu
        button_menu = self.uimanager.get_widget('/ButtonMenu')
        
        menu_button = gtk.MenuToolButton(None, None)
        hbox = menu_button.get_child()
        button, toggle_button = hbox.get_children()
        hbox.remove(button)

        img = gtk.image_new_from_stock(gtk.STOCK_PREFERENCES,
                                       gtk.ICON_SIZE_SMALL_TOOLBAR)

        arrow = toggle_button.get_child()
        toggle_button.remove(arrow)
        hbox = gtk.HBox()
        hbox.add(img)
        #hbox.add(gtk.Label('hello'))
        #hbox.add(arrow)
        toggle_button.add(hbox)
        menu_button.show()
        
        
        toolbar_hbox = wTree.get_widget('hbox3')
        from gui.widgets import PopupMenuButton
        self.ctrl_button = PopupMenuButton(label='oho')
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_MEDIA_RECORD, gtk.ICON_SIZE_BUTTON)
        #self.ctrl_button.set_image(image)
        self.ctrl_button.set_property("image", image)
        menubar = wTree.get_widget('menubar')
        menubar.hide()
        menu = wTree.get_widget('menu-edit')
        #self.ctrl_button.set_menu(menu)
        #toolbar_hbox.pack_end(self.ctrl_button, False)
        toolbar_hbox.pack_end(menu_button, False)
        # Move it to the right
        toolbar_hbox.reorder_child(menu_button, 1)
        menu_button.set_menu(button_menu)
        self.ctrl_button.show()
        
        self.set_tooltips(self.uimanager)
        accelgroup = self.uimanager.get_accel_group()
        self.main_window.add_accel_group(accelgroup)
        


    def onAppQuit(self):
        """ The application is about to terminate """
        prefs.set(__name__, 'volume', self.btnVolume.get_value())


    def onNewTrack(self, track):
        """ A new track is being played """
        ##self.btnStop.set_sensitive(True)
        self.btnPlay.set_sensitive(True)
        self.btnPlay.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, PLAY_PAUSE_ICON_SIZE))
        self.btnPlay.set_tooltip_text(_('Pause the current track'))

        self.currTrackLength = track.getLength()
        self.sclSeek.show()
        ##self.lblElapsed.show()
        ##self.lblRemaining.show()
        self.onNewTrackPosition(0)

        # Must be done last
        if self.currTrackLength != 0:
            self.sclSeek.set_range(0, self.currTrackLength)


    def onStopped(self):
        """ The playback has been stopped """
        ##self.btnStop.set_sensitive(False)
        self.btnNext.set_sensitive(False)
        self.btnPrev.set_sensitive(False)
        self.btnPlay.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, PLAY_PAUSE_ICON_SIZE))
        self.btnPlay.set_tooltip_text(_('Play the first selected track of the playlist'))
        self.sclSeek.hide()
        ##self.lblElapsed.hide()
        ##self.lblRemaining.hide()


    def onNewTrackPosition(self, seconds):
        """ The track position has changed """
        if not self.sclBeingDragged:
            ## Use "1:40 / 2:34" format
            if seconds >= self.currTrackLength:
                seconds = self.currTrackLength
            self.set_time(seconds)
            
            # Make sure the handler will not be called
            self.sclSeek.handler_block_by_func(self.onSeekValueChanged)
            self.sclSeek.set_value(seconds)
            self.sclSeek.handler_unblock_by_func(self.onSeekValueChanged)


    def onVolumeChanged(self, value):
        """ The volume has been changed """
        self.btnVolume.handler_block_by_func(self.onVolumeValueChanged)
        self.btnVolume.set_value(value)
        self.btnVolume.handler_unblock_by_func(self.onVolumeValueChanged)


    def onCurrentTrackMoved(self, hasPrevious, hasNext):
        """ Update previous and next buttons """
        self.btnNext.set_sensitive(hasNext)
        self.btnPrev.set_sensitive(hasPrevious)


    def onPaused(self):
        """ The playback has been paused """
        self.btnPlay.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, PLAY_PAUSE_ICON_SIZE))
        self.btnPlay.set_tooltip_text(_('Continue playing the current track'))


    def onUnpaused(self):
        """ The playback has been unpaused """
        self.btnPlay.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, PLAY_PAUSE_ICON_SIZE))
        self.btnPlay.set_tooltip_text(_('Pause the current track'))


    def onNewTracklist(self, tracks, playtime):
        """ A new tracklist has been set """
        self.btnPlay.set_sensitive(playtime != 0)


    # --== GTK handlers ==--


    def onSeekValueChanged(self, range):
        """ The user has moved the seek slider """
        print 'onSeekValueChanged'
        modules.postMsg(consts.MSG_CMD_SEEK, {'seconds': int(range.get_value())})
        self.sclBeingDragged = False


    def onSeekChangingValue(self, range, scroll, value):
        """ The user is moving the seek slider """        
        self.sclBeingDragged = True

        if value >= self.currTrackLength: value = self.currTrackLength
        else:                             value = int(value)

        ##self.lblElapsed.set_label(sec2str(value))
        ##self.lblRemaining.set_label(sec2str(self.currTrackLength - value))
        self.set_time(value)
        
        
    def onSeekButtonPressed(self, widget, event):
        '''
        Let left-clicks behave as middle-clicks -> Jump to correct position
        '''
        # Leftclick
        if event.button == 1:
            self.sclBeingDragged = True
            event.button = 2
            # Middleclick
            widget.emit('button-press-event', event)
            return True
            
            
    def onSeekButtonReleased(self, widget, event):
        '''
        Let left-clicks behave as middle-clicks -> Jump to correct position
        '''
        # Leftclick
        if event.button == 1:
            self.sclBeingDragged = True
            event.button = 2
            # Middleclick
            widget.emit('button-release-event', event)
            return True


    def onVolumeValueChanged(self, button, value):
        """ The user has moved the volume slider """
        modules.postMsg(consts.MSG_CMD_SET_VOLUME, {'value': value})
        
        
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
