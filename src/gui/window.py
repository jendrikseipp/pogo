# -*- coding: utf-8 -*-
#
# Copyright (c) 2007  François Ingelrest (Francois.Ingelrest@gmail.com)
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

from gi.repository import GObject
from gi.repository import Gtk

import tools


class Window(Gtk.Window):
    """
        Add some functionalities to Gtk.Window:
         * Automatically save and restore size
         * Hide the window instead of destroying it
         * Add a isVisible() function
         * Add a getWidget() function that acts like get_object()
    """

    def __init__(self, resFile, container, modName, title, defaultWidth, defaultHeight):
        """ Constructor """
        GObject.GObject.__init__(self)
        # Load only the top-level container of the given .ui file
        _, self.wBuilder = tools.loadGladeFile(resFile, container)
        self.visible = False
        self.modName = modName
        # Configure the window
        self.set_title(title)
        self.wBuilder.get_object(container).reparent(self)
        if tools.prefs.get(modName, 'win-is-maximized', False):
            self.maximize()
        self.resize(tools.prefs.get(modName, 'win-width', defaultWidth), tools.prefs.get(modName, 'win-height', defaultHeight))
        self.set_position(Gtk.WindowPosition.CENTER)
        # Connect GTK handlers
        self.connect('delete-event',       self.onDelete)
        self.connect('size-allocate',      self.onResize)
        self.connect('window-state-event', self.onState)


    def getWidget(self, name):
        """ Return the widget with the given name """
        return self.wBuilder.get_object(name)


    def isVisible(self):
        """ Return True if the window is currently visible """
        return self.visible


    def show(self):
        """ Show the window if not visible, bring it to top otherwise """
        self.visible = True
        self.show_all()
        self.present()


    def hide(self):
        """ Hide the window """
        self.visible = False
        Gtk.Window.hide(self)


    # --== GTK handlers ==--


    def onResize(self, win, rect):
        """ Save the new size of the dialog """
        if not win.props.is_maximized:
            tools.prefs.set(self.modName, 'win-width',  rect.width)
            tools.prefs.set(self.modName, 'win-height', rect.height)


    def onState(self, win, evt):
        """ Save the new state of the dialog """
        tools.prefs.set(self.modName, 'win-is-maximized', win.props.is_maximized)


    def onDelete(self, win, evt):
        """ Hide the window instead of deleting it """
        self.hide()
        return True
