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

import os

import gtk, gobject

import gui, media, modules, tools, os

from gui             import fileChooser
from tools           import consts, icons
from gettext         import gettext as _
from gobject         import TYPE_STRING, TYPE_INT, TYPE_PYOBJECT
from gui.widgets     import TrackTreeView

MOD_INFO = ('Tracktree', 'Tracktree', '', [], True, False)

# The format of a row in the treeview
(
    ROW_ICO,    # Item icon
    ROW_NAME,   # Item name
    ROW_TRK,    # The track object
) = range(3)


PREFS_DEFAULT_REPEAT_STATUS      = False

# Internal d'n'd (reordering)
DND_REORDERING_ID   = 1024
DND_INTERNAL_TARGET = ('extListview-internal', gtk.TARGET_SAME_WIDGET, DND_REORDERING_ID)


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
                        consts.MSG_CMD_FILE_EXPLORER_DRAG_BEGIN: self.onDragBegin,
                   }

        modules.Module.__init__(self, handlers)
        
        
    def getTracks(self, rows):
        ## Unused
        tracks = []
        for row in rows:
            track = self.tree.getTrack(row)
            if track:
                tracks.append(track)
        return tracks
        
    
    def getTrackDir(self, root=None):
        flat = False if root else True
        name = self.tree.getLabel(root) if root else 'playtree'
        name = name.replace('<b>', '').replace('</b>', '')
        trackdir = media.TrackDir(name=name, flat=flat)
        
        for iter in self.tree.iter_children(root):
            track = self.tree.getTrack(iter)
            if track:
                trackdir.tracks.append(track)
            else:
                subdir = self.getTrackDir(iter)
                trackdir.subdirs.append(subdir)
        
        return trackdir
        

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
            
            
    def set_track_playing(self, iter, playing):
        if not iter:
            return
        track = self.tree.getTrack(iter)
        if not track:
            return
            
        for parent in self.tree.get_all_parents(iter):
            parent_label = self.tree.getLabel(parent)
            parent_label = tools.htmlUnescape(parent_label)
            is_bold = parent_label.startswith('<b>') and parent_label.endswith('</b>')
            if playing and not is_bold:
                parent_label = tools.htmlEscape(parent_label)
                self.tree.setLabel(parent, '<b>%s</b>' % parent_label)
            elif not playing and is_bold:
                parent_label = tools.htmlEscape(parent_label[3:-4])
                self.tree.setLabel(parent, parent_label)
            
        parent = self.tree.store.iter_parent(iter)
        parent_label = self.tree.getLabel(parent) if parent else None
        label = track.get_label(parent_label=parent_label, playing=playing)
        if playing:
            self.tree.setLabel(iter, label)
            self.tree.setItem(iter, ROW_ICO, icons.playMenuIcon())
            self.tree.expand(iter)
        else:
            self.tree.setLabel(iter, label)
            icon = self.tree.getItem(iter, ROW_ICO)
            has_error = (icon == icons.errorMenuIcon())
            is_dir = (icon == icons.mediaDirMenuIcon())
            if not is_dir and not has_error:
                self.tree.setItem(iter, ROW_ICO, icons.nullMenuIcon())
        


    def jumpTo(self, iter, sendPlayMsg=True):
        """ Jump to the track located at the given iter """
        if not iter:
            return
            
        mark = self.tree.getMark()
        if mark:
            self.set_track_playing(mark, False)
            
        self.tree.setMark(iter)
        self.tree.scroll(iter)
            
        # Check track
        track = self.tree.getTrack(iter)
        if not track:
            # Row may be a directory
            self.jumpTo(self.__getNextTrackIter())
            return
            
        self.set_track_playing(iter, True)

        if sendPlayMsg:
            modules.postMsg(consts.MSG_CMD_PLAY, {'uri': track.getURI()})

        modules.postMsg(consts.MSG_EVT_NEW_TRACK,   {'track': track})
        modules.postMsg(consts.MSG_EVT_TRACK_MOVED, {'hasPrevious': self.__hasPreviousTrack(), 'hasNext': self.__hasNextTrack()})
        
    def insert(self, tracks, target=None, drop_mode=None, playNow=True, highlight=False):
        if type(tracks) == list:
            trackdir = media.TrackDir(None, flat=True)
            trackdir.tracks = tracks
            tracks = trackdir
            
        self.insertDir(tracks, target, drop_mode, highlight)
        self.onListModified()
        
        # TODO: Find out which node to highlight
        return
            
        # TODO: playNow wanted? Buggy in current state
        if playNow:
            if parent is None:
                dest = self.tree.get_lowest_root()
            else:
                dest = self.tree.get_last_child_iter(parent)
            self.jumpTo(dest)
            
    def insertDir(self, trackdir, target=None, drop_mode=None, highlight=False):
        '''
        Insert a directory recursively, return the iter of the first
        added element
        '''
        model = self.tree.store
        if trackdir.flat:
            new = target
        else:
            string = trackdir.dirname.replace('_', ' ')
            string = tools.htmlEscape(string)
            source_row = (icons.mediaDirMenuIcon(), string, None)
            
            new = self.tree.insert(target, source_row, drop_mode)
            drop_mode = gtk.TREE_VIEW_DROP_INTO_OR_AFTER
            if highlight:
                gobject.idle_add(self.tree.get_selection().select_iter, new)
        
        dest = new
        for index, subdir in enumerate(trackdir.subdirs):
            drop = drop_mode if index == 0 else gtk.TREE_VIEW_DROP_AFTER
            dest = self.insertDir(subdir, dest, drop)
            
        dest = new
        for index, track in enumerate(trackdir.tracks):
            drop = drop_mode if index == 0 else gtk.TREE_VIEW_DROP_AFTER
            dest = self.insertTrack(track, dest, drop)
            
        if not trackdir.flat:
            # Open albums on the first layer
            if target is None or model.iter_depth(new) == 0:
                self.tree.expand(new)
        
        return new
        
        
    def insertTrack(self, track, target=None, drop_mode=None, highlight=False):
        '''
        Insert a new track into the tracktree under parentPath
        '''
        length = track.getLength()
        self.playtime += length
        
        name = track.get_label()
        
        row = (icons.nullMenuIcon(), name, track)
        new_iter = self.tree.insert(target, row, drop_mode)
        parent = self.tree.store.iter_parent(new_iter)
        if parent:
            # adjust track label to parent
            parent_label = self.tree.getLabel(parent)
            new_label = track.get_label(parent_label)
            self.tree.setLabel(new_iter, new_label)
        if highlight:
            #path = self.tree.store.get_path(new_iter)
            gobject.idle_add(self.tree.get_selection().select_iter, new_iter)
        return new_iter


    def set(self, tracks, playNow):
        """ Replace the tracklist, clear it if tracks is None """
        self.playtime = 0
        
        if type(tracks) == list:
            trackdir = media.TrackDir(None, flat=True)
            trackdir.tracks = tracks
            tracks = trackdir

        if self.tree.hasMark() and ((not playNow) or (tracks is None) or tracks.empty()):
            modules.postMsg(consts.MSG_CMD_STOP)

        self.tree.clear()
        
        if tracks is not None and not tracks.empty():
            self.insert(tracks)
            
        self.tree.collapse_all()
            
        self.onListModified()


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
        
        iters = [iter] if iter else list(self.tree.iterSelectedRows())
        
        # reverse list, so that we remove children before their fathers
        for iter in reversed(iters):
            track = self.tree.getTrack(iter)
            if track:
                self.playtime -= track.getLength()
            self.tree.removeRow(iter)

        self.tree.selection.unselect_all()

        if hadMark and not self.tree.hasMark():
            modules.postMsg(consts.MSG_CMD_STOP)
            
        self.onListModified()


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

        #popup.append(gtk.SeparatorMenuItem())

        # Clear
        clear = gtk.ImageMenuItem(_('Clear Playlist'))
        clear.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_MENU))
        popup.append(clear)

        if len(tree.store) == 0:
            clear.set_sensitive(False)
        else:
            clear.connect('activate', lambda item: modules.postMsg(consts.MSG_CMD_TRACKLIST_CLR))

        #popup.append(gtk.SeparatorMenuItem())

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
                
                
    def restore_expanded_rows(self):
        print 'PATHS', self.tree.expanded_rows
        for path in self.tree.expanded_rows:
            print 'EXPANDING', path
            self.tree.expand(path)
        self.tree.expanded_rows = None


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
                   (None, [(None, TYPE_PYOBJECT)], False),
                  )
        
        self.tree = TrackTreeView(columns, use_markup=True)
        self.tree.enableDNDReordering()
        #self.tree.setDNDSources([consts.DND_TARGETS[consts.DND_POGO_TRACKS]])
        self.tree.setDNDSources([DND_INTERNAL_TARGET])
        
        wTree.get_widget('scrolled-tracklist').add(self.tree)
        
        # GTK handlers
        #self.tree.connect('row-activated', self.on_row_activated)
        #self.tree.store.connect('row-inserted', self.on_row_inserted)
        #self.tree.store.connect('row-deleted', self.on_row_deleted)
        
        #self.tree.selection.connect('changed', self.onSelectionChanged)
         
        self.tree.connect('exttreeview-button-pressed', self.onMouseButton)
        self.tree.connect('tracktreeview-dnd', self.onDND)
        self.tree.connect('key-press-event', self.onKeyboard)
        #self.tree.connect('extlistview-modified', self.onListModified)
        #self.tree.connect('button-pressed', self.onButtonPressed)
        
        #self.btnClear.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_TRACKLIST_CLR))
        #self.btnRepeat.connect('toggled', self.onButtonRepeat)
        #self.btnShuffle.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_TRACKLIST_SHUFFLE))
        # Restore preferences
        #self.btnRepeat.set_active(tools.prefs.get(__name__, 'repeat-status', PREFS_DEFAULT_REPEAT_STATUS))
        # Set icons
        #wTree.get_widget('img-repeat').set_from_icon_name('stock_repeat', gtk.ICON_SIZE_BUTTON)
        #wTree.get_widget('img-shuffle').set_from_icon_name('stock_shuffle', gtk.ICON_SIZE_BUTTON)
        
        # Hide stop button (like in banshee, rhythmbox and itunes)
        ##self.stop_button = wTree.get_widget('btn-stop')
        ##self.stop_button.hide()


    def onTrackEnded(self, withError):
        """ The current track has ended, jump to the next one if any """
        current_iter = self.tree.getMark()

        # If an error occurred with the current track, flag it as such
        if withError and current_iter:
            self.tree.setItem(current_iter, ROW_ICO, icons.errorMenuIcon())

        # Find the next 'playable' track (not already flagged)
        next = self.__getNextTrackIter()
        if next:
            send_play_msg = True
            if current_iter:
                track_name = self.tree.getTrack(current_iter).getURI()
                send_play_msg = (track_name != self.bufferedTrack)
            self.jumpTo(next, sendPlayMsg=send_play_msg)
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
            self.set_track_playing(currTrack, False)
            #if self.tree.getItem(currTrack, ROW_ICO) != icons.errorMenuIcon():
            #    self.tree.setItem(currTrack, ROW_ICO, icons.nullMenuIcon())
            self.tree.clearMark()


    def onPausedToggled(self, icon):
        """ Switch between paused and unpaused """
        if self.tree.hasMark():
            self.tree.setItem(self.tree.getMark(), ROW_ICO, icon)
            
            
    def onDragBegin(self, paths):
        dir_selected = any(map(os.path.isdir, paths))
        self.tree.dir_selected = dir_selected
        if dir_selected:
            # Save expanded rows
            def expanded(treeview, path):
                print 'APPEND', path
                row = self.tree.store.get_iter(path)
                self.tree.expanded_rows.append(row)
            
            self.tree.expanded_rows = []
            self.tree.map_expanded_rows(expanded)
            print 'PATHS =', self.tree.expanded_rows
        
            self.tree.collapse_all()


    # --== GTK handlers ==--
            
        
    def onMouseButton(self, tree, event, path):
        """ A mouse button has been pressed """
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS and path is not None:
            self.jumpTo(self.tree.store.get_iter(path))
        elif event.button == 3:
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
        
        # Update playlist length and playlist position for all tracks
        #for position, row in enumerate(self.tree):
        #    row[ROW_TRK].setPlaylistPos(position + 1)
        #    row[ROW_TRK].setPlaylistLen(len(self.tree))
        tracks = self.getTrackDir()
        
        modules.postMsg(consts.MSG_EVT_NEW_TRACKLIST, {'tracks': tracks, 'playtime': self.playtime})

        if self.tree.hasMark():
            modules.postMsg(consts.MSG_EVT_TRACK_MOVED, {'hasPrevious': self.__hasPreviousTrack(), 'hasNext':  self.__hasNextTrack()})


    #def onSelectionChanged(self, selection):
    #    """ The selection has changed """
    #    rows = self.tree.getSelectedRows()
    #    tracks = self.getTracks(rows)
    #    modules.postMsg(consts.MSG_EVT_TRACKLIST_NEW_SEL, {'tracks': tracks})


    def onDND(self, list, context, x, y, dragData, dndId, time):
        """ External Drag'n'Drop """
        import urllib

        if dragData.data == '':
            context.finish(False, False, time)
            return

        # A list of filenames, without 'file://' at the beginning
        if dndId == consts.DND_POGO_URI:
            tracks = media.getTracks([urllib.url2pathname(uri) for uri in dragData.data.split()])
        # A list of filenames starting with 'file://'
        elif dndId == consts.DND_URI:
            tracks = media.getTracks([urllib.url2pathname(uri)[7:] for uri in dragData.data.split()])
        # A list of tracks
        elif dndId == consts.DND_POGO_TRACKS:
            tracks = [media.track.unserialize(serialTrack) for serialTrack in dragData.data.split('\n')]

        # dropInfo is tuple (path, drop_pos)
        dropInfo = list.get_dest_row_at_pos(x, y)

        # Insert the tracks, but beware of the AFTER/BEFORE mechanism used by GTK
        if dropInfo is None:
            self.insert(tracks, highlight=True)
        else:
            path, drop_mode = dropInfo
            iter = self.tree.store.get_iter(path)
            self.insert(tracks, iter, drop_mode, highlight=True)
            
        #self.restore_expanded_rows()

        context.finish(True, False, time)
