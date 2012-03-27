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

import gtk, modules, os.path, tools

from tools import consts, prefs

MOD_INFO = ('Track Panel', 'Track Panel', '', [], True, False)


class TrackPanel(modules.Module):
    """
        This module manages the panel showing information on the current track.
        This includes the thumbnail of the current cover, if the user has enabled the 'Covers' module.
    """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_STOPPED:     self.onStopped,
                        consts.MSG_CMD_SET_COVER:   self.onSetCover,
                        consts.MSG_EVT_NEW_TRACK:   self.onNewTrack,
                        consts.MSG_EVT_APP_STARTED: self.onAppStarted,
                        consts.MSG_EVT_APP_QUIT:    self.onAppQuit,
                   }

        modules.Module.__init__(self, handlers)


    # --== Message handlers ==--


    def onAppStarted(self):
        """ Real initialization function, called when this module has been loaded """
        # Widgets
        self.currTrack = None

        show_thumb = prefs.get(__name__, 'show_thumb', True)
        self.cover_spot = CoverSpot(show_thumb)

    def onAppQuit(self):
        """ The application is about to terminate """
        prefs.set(__name__, 'show_thumb', self.cover_spot.show_thumb)


    def onNewTrack(self, track):
        """ A new track is being played """
        self.currTrack = track


    def onStopped(self):
        """ Playback has been stopped """
        self.currTrack = None
        self.cover_spot.set_images(None, None)


    def onSetCover(self, track, pathThumbnail, pathFullSize):
        """ Set the cover that is currently displayed """
        # Must check if currTrack is not None, because '==' calls the cmp() method and this fails on None
        if self.currTrack is not None and track == self.currTrack:
            self.cover_spot.set_images(pathFullSize, pathThumbnail)

            # Create symbolic links to these covers so that external apps can access them
            if pathFullSize is not None and pathThumbnail is not None:
                ext = os.path.splitext(pathFullSize)[1]
                extThumb = os.path.splitext(pathThumbnail)[1]

                link = os.path.join(consts.dirCfg, 'current-cover' + ext)
                linkThumb = os.path.join(consts.dirCfg, 'current-cover-small' + extThumb)

                tools.remove(link)
                tools.remove(linkThumb)

                os.symlink(pathFullSize, link)
                os.symlink(pathThumbnail, linkThumb)



class CoverSpot(object):
    def __init__(self, show_thumb):
        self.show_thumb = show_thumb
        self.has_focus = True

        self.cover_window = CoverWindow()
        self.thumb_window = CoverWindow()

        # Switch sizes, when clicked
        self.cover_window.evtBox.connect('button-press-event', self.onCoverClicked, True)
        self.thumb_window.evtBox.connect('button-press-event', self.onCoverClicked, False)

        wTree = tools.prefs.getWidgetsTree()
        main_win = wTree.get_object('win-main')

        main_win.connect('focus-out-event', self.on_focus_out)
        main_win.connect('focus-in-event', self.on_focus_in)
        main_win.connect('size-allocate', self.on_resize)


    def set_images(self, cover_path, thumb_path):
        self.cover_window.set_image(cover_path)
        self.thumb_window.set_image(thumb_path)

        # This somehow fixes the compiz problem where the cover was only
        # shown after the window had been redrawn
        #self.thumb_window.update_position()
        #self.thumb_window.show()
        #self.cover_window.update_position()
        #self.cover_window.show()

        if self.has_focus:
            self.onCoverClicked(None, None, self.show_thumb)


    def onCoverClicked(self, widget, event, show_thumb):
        """ Destroy the cover window """
        if show_thumb:
            self.thumb_window.show()
            self.thumb_window.update_position()
            self.cover_window.hide()
        else:
            self.cover_window.show()
            self.cover_window.update_position()
            self.thumb_window.hide()
        self.show_thumb = show_thumb


    def on_focus_out(self, widget, event):
        self.has_focus = False
        self.cover_window.hide()
        self.thumb_window.hide()


    def on_focus_in(self, widget, event):
        self.has_focus = True
        self.onCoverClicked(None, None, self.show_thumb)


    def on_resize(self, win, rectangle):
        self.cover_window.update_position()
        self.thumb_window.update_position()



class CoverWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        frame = gtk.Frame()
        self.evtBox = gtk.EventBox()
        self.image = gtk.Image()
        self.set_image(None)
        self.evtBox.add(self.image)
        frame.set_shadow_type(gtk.SHADOW_IN)
        frame.add(self.evtBox)
        self.add(frame)

        self.has_cover = False


    def set_image(self, path):
        """
        Change the current image to imgPath.
        Use the application's icon if imgPath is None.
        """
        if path is None:
            self.image.set_from_file(os.path.join(tools.consts.dirPix, 'cover-none.png'))
            # If there is no album to show, hide window
            self.hide()
            self.has_cover = False
        else:
            self.image.set_from_file(path)
            self.update_position()
            self.has_cover = True


    def update_position(self):
        # Make the window exactly as big as the image, not bigger
        self.resize(2, 2)

        # Use default when tree is not yet realized
        x, y = 0,0

        # Position the window in the bottom right corner
        wTree = tools.prefs.getWidgetsTree()
        scrolled = wTree.get_object('scrolled-tracklist')
        tree = scrolled.get_child()
        if tree:
            tree_x, tree_y, tree_width, tree_height = tree.get_allocation()
            # Get the window, the tracktree is painted on
            tree_win = tree.get_parent_window()

            # Get absolute position of the gtk.gdk.Window without the window decos
            orig_tree_win_x, orig_tree_win_y = tree_win.get_origin()

            # Calculate absolute position of upper left corner
            x = orig_tree_win_x + tree_x
            y = orig_tree_win_y + tree_y

            # get lower right corner
            x, y = x + tree_width, y + tree_height

            # leave a little padding space
            x, y = x-10, y-9

        pixbuf = self.image.get_pixbuf()
        width  = pixbuf.get_width()
        height = pixbuf.get_height()
        self.move(int(x - width), int(y - height))


    def show(self):
        if self.has_cover:
            gtk.Window.show_all(self)
