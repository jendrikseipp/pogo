# -*- coding: utf-8 -*-
#
# Author: Ingelrest François (Francois.Ingelrest@gmail.com)
#         Jendrik Seipp (jendrikseipp@web.de)
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

import gtk, gui, media, modules, tools, os

from gui             import fileChooser
from tools           import consts, icons
from gettext         import gettext as _
from gobject         import TYPE_STRING, TYPE_INT, TYPE_PYOBJECT
from gui.widgets     import TrackTreeView

MOD_INFO = ('Tracktree', 'Tracktree', '', [], True, False)

# The format of a row in the treeview
(
    ROW_ICO, # Item icon
    ROW_NAME,     # Item name
    ROW_TYPE,     # The type of the item (e.g., directory, file)
    ROW_FULLPATH,  # The full path to the item
    ROW_TRK,   # The track object
) = range(5)


PREFS_DEFAULT_REPEAT_STATUS      = False



class Tracktree(modules.Module):
    """ This module manages the tracklist """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_CMD_NEXT:              self.jumpToNext,
                        consts.MSG_EVT_PAUSED:            lambda: self.onPausedToggled(icons.pauseMenuIcon()),
                        consts.MSG_EVT_STOPPED:           self.onStopped,
                        consts.MSG_EVT_UNPAUSED:          lambda: self.onPausedToggled(icons.playMenuIcon()),
                        consts.MSG_CMD_PREVIOUS:          self.jumpToPrevious,
                        consts.MSG_EVT_NEED_BUFFER:       self.onBufferingNeeded,
                        consts.MSG_EVT_APP_STARTED:       self.onAppStarted,
                        consts.MSG_CMD_TOGGLE_PAUSE:      self.togglePause,
                        consts.MSG_CMD_TRACKLIST_DEL:     self.remove,
                        consts.MSG_CMD_TRACKLIST_ADD:     self.insert,
                        consts.MSG_CMD_TRACKLIST_SET:     self.set,
                        consts.MSG_CMD_TRACKLIST_CLR:     lambda: self.set(None, None),
                        consts.MSG_EVT_TRACK_ENDED_OK:    lambda: self.onTrackEnded(False),
                        #consts.MSG_CMD_TRACKLIST_REPEAT:  self.setRepeat,
                        consts.MSG_EVT_TRACK_ENDED_ERROR: lambda: self.onTrackEnded(True),
                        #consts.MSG_CMD_TRACKLIST_SHUFFLE: self.shuffleTracklist,
                   }

        modules.Module.__init__(self, handlers)
        
        
    def getTracks(self, rows):
        tracks = []
        for row in rows:
            track = self.tree.getItem(row, ROW_TRK)
            if track:
                tracks.append(track)
        return tracks
        
        
    def getAllTracks(self):
        self.tree.selection.select_all()
        rows = self.tree.getSelectedRows()
        self.tree.selection.unselect_all()
        return self.getTracks(rows)
        
        mark = self.tree.getMark()
        self.tree.setMark(None)
        tracks = []
        next = self.__getNextTrackIter()
        #while next:


    def __getNextTrackIter(self):
        """ Return the index of the next track, or -1 if there is none """
        next = None
        while True:
            next = self.tree.get_next_iter(next)
            if not next:
                return None
            
            # Check track
            error = self.tree.getItem(next, ROW_ICO) == icons.errorMenuIcon()
            track = self.tree.getItem(next, ROW_TRK)
            if track and not error:
                # Row is not a directory
                return next


    def __hasNextTrack(self):
        """ Return whether there is a next track """
        return self.__getNextTrackIter() is not None


    def __getPreviousTrackIter(self):
        """ Return the index of the previous track, or -1 if there is none """
        prev = None
        while True:
            prev = self.tree.get_prev_iter(prev)
            if not prev:
                return None
            
            # Check track
            error = self.tree.getItem(prev, ROW_ICO) == icons.errorMenuIcon()
            track = self.tree.getItem(prev, ROW_TRK)
            if track and not error:
                # Row is not a directory
                return prev


    def __hasPreviousTrack(self):
        """ Return whether there is a previous track """
        return self.__getPreviousTrackIter() is not None


    def jumpToNext(self):
        """ Jump to the next track, if any """
        where = self.__getNextTrackIter()
        if where:
            self.jumpTo(where)


    def jumpToPrevious(self):
        """ Jump to the previous track, if any """
        where = self.__getPreviousTrackIter()
        if where:
            self.jumpTo(where)


    def jumpTo(self, iter, sendPlayMsg=True):
        """ Jump to the track located at the given iter """
        print 'JUMPING TO', self.tree.get_nodename(iter)
        if not iter:
            return
            
        mark = self.tree.getMark()
        if mark:
            icon = self.tree.getItem(mark, ROW_ICO)
            has_error = (icon == icons.errorMenuIcon())
            is_dir = (icon == icons.mediaDirMenuIcon())
            if not is_dir and not has_error:
                self.tree.setItem(mark, ROW_ICO, icons.nullMenuIcon())
            
        self.tree.setMark(iter)
        self.tree.scroll(iter)
            
        # Check track
        track = self.tree.getItem(iter, ROW_TRK)
        if not track:
            # Row may be a directory
            self.jumpTo(self.__getNextTrackIter())
            return
            
        self.tree.setItem(iter, ROW_ICO, icons.playMenuIcon())
        self.tree.expand(iter)

        if sendPlayMsg:
            modules.postMsg(consts.MSG_CMD_PLAY, {'uri': track.getURI()})

        modules.postMsg(consts.MSG_EVT_NEW_TRACK,   {'track': track})
        modules.postMsg(consts.MSG_EVT_TRACK_MOVED, {'hasPrevious': self.__hasPreviousTrack(), 'hasNext': self.__hasNextTrack()})
        
    def insert(self, tracks, playNow, parent=None):
        if type(tracks) == list:
            trackdir = media.TrackDir(None, flat=True)
            trackdir.tracks = tracks
            tracks = trackdir
            
        self.insertDir(tracks, parent)
        return
            
        # TODO: playNow wanted? Buggy in current state
        if playNow:
            if parent is None:
                dest = self.tree.get_lowest_root()
            else:
                dest = self.tree.get_last_child_iter(parent)
            self.jumpTo(dest)
            
    def insertDir(self, trackdir, parent=None):
        '''
        Insert a directory recursively, return the iter of the first
        added element
        '''
        if trackdir.flat:
            dir_iter = parent
        else:
            dir_iter = self.tree.appendRow((icons.mediaDirMenuIcon(), trackdir.dirname, 1, 'something', None), parent)
        
        for subdir in trackdir.subdirs:
            self.insertDir(subdir, dir_iter)
        for track in trackdir.tracks:
            self.insertTrack(track, dir_iter)
            
        if not trackdir.flat:
            if parent is None: 
                self.tree.expand(dir_iter)
        
    def insertTrack(self, track, parentPath=None):
        '''
        Insert a new track into the tracktree under parentPath
        '''
        ##rows = [[icons.nullMenuIcon(), track.getNumber(), track.getTitle(), track.getArtist(), track.getExtendedAlbum(),
        ##            track.getLength(), track.getBitrate(), track.getGenre(), track.getDate(), track.getURI(), track] for track in tracks]
        self.playtime += track.getLength()
        trackURI = track.getURI()
        trackString = os.path.basename(trackURI)
        self.tree.appendRow((icons.nullMenuIcon(), trackString, 1, 'something', track), parentPath)


    def set(self, tracks, playNow):
        """ Replace the tracklist, clear it if tracks is None """
        self.playtime = 0
        
        if type(tracks) == list:
            trackdir = media.TrackDir(None, flat=True)
            trackdir.tracks = tracks
            tracks = trackdir
        
        print 'SET TRACKS'
        print tracks

        if self.tree.hasMark() and ((not playNow) or (tracks is None) or tracks.empty()):
            modules.postMsg(consts.MSG_CMD_STOP)

        self.tree.clear()
        
        if tracks is not None and not tracks.empty():
            self.insert(tracks, playNow)


    def savePlaylist(self):
        """ Save the current tracklist to a playlist """
        outFile = fileChooser.save(self.window, _('Save playlist'), 'playlist.m3u')

        if outFile is not None:
            allFiles = [row[ROW_TRK].getFilePath() for row in self.tree.iterAllRows()]
            media.playlist.save(allFiles, outFile)


    def remove(self, iter=None):
        """ Remove the given track, or the selection if iter is None """
        hadMark = self.tree.hasMark()
        #self.previousTracklist = [row[ROW_TRK] for row in self.tree]

        if iter is not None:
            track = self.tree.getItem(iter, ROW_TRK)
            if track:
                self.playtime -= track.getLength()
            self.tree.removeRow(iter)
        else:
            tracks = [self.tree.getItem(iter, ROW_TRK) for iter in self.tree.iterSelectedRows()]
            self.playtime -= sum([track.getLength() for track in tracks if track])
            self.tree.removeSelectedRows()

        self.tree.selection.unselect_all()

        if hadMark and not self.tree.hasMark():
            modules.postMsg(consts.MSG_CMD_STOP)


    def onShowPopupMenu(self, tree, button, time, path):
        """ The index parameter may be None """
        if path is None:
            iter = None
        else:
            iter = tree.store.get_iter(path)
        
        popup = gtk.Menu()

        # Remove
        remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        popup.append(remove)

        if iter is None:
            remove.set_sensitive(False)
        else:
            remove.connect('activate', lambda item: self.remove())

        popup.append(gtk.SeparatorMenuItem())

        # Clear
        clear = gtk.ImageMenuItem(_('Clear Playlist'))
        clear.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_MENU))
        popup.append(clear)

        if len(tree.store) == 0:
            clear.set_sensitive(False)
        else:
            clear.connect('activate', lambda item: modules.postMsg(consts.MSG_CMD_TRACKLIST_CLR))

        popup.append(gtk.SeparatorMenuItem())

        # Save
        #save = gtk.ImageMenuItem(_('Save Playlist As...'))
        #save.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE_AS, gtk.ICON_SIZE_MENU))
        #popup.append(save)

        #if len(list) == 0: save.set_sensitive(False)
        #else:              save.connect('activate', lambda item: self.savePlaylist())

        popup.show_all()
        popup.popup(None, None, None, button, time)


    def togglePause(self):
        """ Start playing if not already playing """
        if not self.tree.hasMark():
            if self.tree.selection.count_selected_rows() > 0:
                model, sel_rows_list = self.tree.selection.get_selected_rows()
                first_sel_iter = self.tree.store.get_iter(sel_rows_list[0])
                self.jumpTo(first_sel_iter)
            else:
                self.jumpTo(self.tree.get_first_iter())


    # --== Message handlers ==--


    def onAppStarted(self):
        """ This is the real initialization function, called when the module has been loaded """
        wTree                  = tools.prefs.getWidgetsTree()
        self.playtime          = 0
        self.bufferedTrack     = None
        self.previousTracklist = None
        # Retrieve widgets
        self.window     = wTree.get_widget('win-main')
        self.btnClear   = wTree.get_widget('btn-tracklistClear')
        self.btnRepeat  = wTree.get_widget('btn-tracklistRepeat')
        self.btnShuffle = wTree.get_widget('btn-tracklistShuffle')

        columns = (('',   [(gtk.CellRendererPixbuf(), gtk.gdk.Pixbuf), (gtk.CellRendererText(), TYPE_STRING)], True),
                   (None, [(None, TYPE_INT)],                                                                 False),
                   (None, [(None, TYPE_STRING)],                                                               False),
                   (None, [(None, TYPE_PYOBJECT)], False),
                  )
        
        self.tree = TrackTreeView(columns, use_markup=True)
        ##self.tree.get_column(4).set_cell_data_func(txtRRdr, self.__fmtLengthColumn)
        ##self.tree.enableDNDReordering()
        wTree.get_widget('scrolled-tracklist').add(self.tree)
        # GTK handlers
        self.tree.connect('row-activated', self.on_row_activated)
        self.tree.store.connect('row-inserted', self.on_row_inserted)
        self.tree.store.connect('row-deleted', self.on_row_deleted)
        
        self.tree.selection.connect('changed', self.onSelectionChanged)
        
        
         
        self.tree.connect('exttreeview-button-pressed', self.onMouseButton)
        self.tree.connect('extlistview-dnd', self.onDND)
        self.tree.connect('key-press-event', self.onKeyboard)
        self.tree.connect('extlistview-modified', self.onListModified)
        #self.tree.connect('button-pressed', self.onButtonPressed)
        
        #self.btnClear.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_TRACKLIST_CLR))
        #self.btnRepeat.connect('toggled', self.onButtonRepeat)
        #self.btnShuffle.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_TRACKLIST_SHUFFLE))
        # Restore preferences
        #self.btnRepeat.set_active(tools.prefs.get(__name__, 'repeat-status', PREFS_DEFAULT_REPEAT_STATUS))
        # Set icons
        #wTree.get_widget('img-repeat').set_from_icon_name('stock_repeat', gtk.ICON_SIZE_BUTTON)
        #wTree.get_widget('img-shuffle').set_from_icon_name('stock_shuffle', gtk.ICON_SIZE_BUTTON)
        
        # Hide stop button
        self.stop_button = wTree.get_widget('btn-stop')
        self.stop_button.hide()


    def onTrackEnded(self, withError):
        """ The current track has ended, jump to the next one if any """
        current_iter = self.tree.getMark()

        # If an error occurred with the current track, flag it as such
        if withError:
            self.tree.setItem(current_iter, ROW_ICO, icons.errorMenuIcon())

        # Find the next 'playable' track (not already flagged)
        next = self.__getNextTrackIter()
        if next:
            track = self.tree.getItem(current_iter, ROW_TRK).getURI()
            self.jumpTo(next, sendPlayMsg=(track != self.bufferedTrack))
            self.bufferedTrack = None
            return

        self.bufferedTrack = None
        modules.postMsg(consts.MSG_CMD_STOP)


    def onBufferingNeeded(self):
        """ The current track is close to its end, so we try to buffer the next one to avoid gaps """
        where = self.__getNextTrackIter()
        if where:
            self.bufferedTrack = self.tree.getItem(where, ROW_TRK).getURI()
            modules.postMsg(consts.MSG_CMD_BUFFER, {'uri': self.bufferedTrack})


    def onStopped(self):
        """ Playback has been stopped """
        if self.tree.hasMark():
            currTrack = self.tree.getMark()
            if self.tree.getItem(currTrack, ROW_ICO) != icons.errorMenuIcon():
                self.tree.setItem(currTrack, ROW_ICO, icons.nullMenuIcon())
            self.tree.clearMark()


    def onPausedToggled(self, icon):
        """ Switch between paused and unpaused """
        if self.tree.hasMark():
            self.tree.setItem(self.tree.getMark(), ROW_ICO, icon)


    # --== GTK handlers ==--
    
    def on_row_activated(self, treeview, path, view_column):
        self.jumpTo(self.tree.model.get_iter(path))
        
    def on_row_inserted(self, store, path, iter):
        self.onListModified()
        
    def on_row_deleted(self, store, path):
        self.onListModified()
        
        
    def onMouseButton(self, tree, event, path):
        """ A mouse button has been pressed """
        if event.button == 3:
            self.onShowPopupMenu(tree, event.button, event.time, path)


    def onKeyboard(self, list, event):
        """ Keyboard shortcuts """
        keyname = gtk.gdk.keyval_name(event.keyval)

        if keyname == 'Delete':   self.remove()
        elif keyname == 'Return': self.jumpTo(self.tree.getFirstSelectedRow())
        elif keyname == 'space':  modules.postMsg(consts.MSG_CMD_TOGGLE_PAUSE)
        elif keyname == 'Escape': modules.postMsg(consts.MSG_CMD_STOP)
        elif keyname == 'Left':   modules.postMsg(consts.MSG_CMD_STEP, {'seconds': -5})
        elif keyname == 'Right':  modules.postMsg(consts.MSG_CMD_STEP, {'seconds': 5})


    def onListModified(self):
        """ Some rows have been added/removed/moved """
        #self.btnClear.set_sensitive(len(list) != 0)
        #self.btnShuffle.set_sensitive(len(list) != 0)

        # Update playlist length and playlist position for all tracks
        #for position, row in enumerate(self.tree):
        #    row[ROW_TRK].setPlaylistPos(position + 1)
        #    row[ROW_TRK].setPlaylistLen(len(self.tree))

        allTracks = self.getAllTracks()
        modules.postMsg(consts.MSG_EVT_NEW_TRACKLIST, {'tracks': allTracks, 'playtime': self.playtime})

        if self.tree.hasMark():
            modules.postMsg(consts.MSG_EVT_TRACK_MOVED, {'hasPrevious': self.__hasPreviousTrack(), 'hasNext':  self.__hasNextTrack()})


    def onSelectionChanged(self, selection):
        """ The selection has changed """
        rows = self.tree.getSelectedRows()
        tracks = self.getTracks(rows)
        modules.postMsg(consts.MSG_EVT_TRACKLIST_NEW_SEL, {'tracks': tracks})


    def onDND(self, list, context, x, y, dragData, dndId, time):
        """ External Drag'n'Drop """
        import urllib

        if dragData.data == '':
            context.finish(False, False, time)
            return

        # A list of filenames, without 'file://' at the beginning
        if dndId == consts.DND_DAP_URI:
            tracks = media.getTracks([urllib.url2pathname(uri) for uri in dragData.data.split()])
        # A list of filenames starting with 'file://'
        elif dndId == consts.DND_URI:
            tracks = media.getTracks([urllib.url2pathname(uri)[7:] for uri in dragData.data.split()])
        # A list of tracks
        elif dndId == consts.DND_DAP_TRACKS:
            tracks = [media.track.unserialize(serialTrack) for serialTrack in dragData.data.split('\n')]

        # dropInfo is tuple (path, drop_pos)
        dropInfo = list.get_dest_row_at_pos(x, y)
        
        # Always append the tracks
        dropInfo = None

        # Insert the tracks, but beware of the AFTER/BEFORE mechanism used by GTK
        if dropInfo is None:
            self.insert(tracks, False)
        else:
            path, drop_pos = dropInfo
            iter = self.tree.store.get_iter(path)
            if drop_pos == gtk.TREE_VIEW_DROP_AFTER:
                self.insert(tracks, False, iter)#dropInfo[0][0] + 1)
            else:
                self.insert(tracks, False, iter)

        context.finish(True, False, time)
