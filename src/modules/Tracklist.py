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

import gtk, gui, media, modules, os.path, tools

from tools           import consts, icons
from gettext         import gettext as _
from gobject         import TYPE_STRING, TYPE_INT, TYPE_PYOBJECT
from media.track     import Track
from gui.extListview import ExtListView

MOD_INFO = ('Tracklist', 'Tracklist', '', [], True, False)

# Create a unique ID for each field of a row in the list
(
    ROW_ICO,   # Icon drawn in front of the row
    ROW_NUM,   # Track number
    ROW_TIT,   # Track title
    ROW_ART,   # Track artist
    ROW_ALB,   # Track album
    ROW_LEN,   # Track length in seconds
    ROW_BTR,   # Bit rate
    ROW_GNR,   # Genre
    ROW_DAT,   # Date
    ROW_PTH,   # Path to the file
    ROW_TRK    # The Track object
) = range(11)

# Create a unique ID for each column that the user can actually see
(
    COL_TRCK_NUM,
    COL_TITLE,
    COL_ARTIST,
    COL_ALBUM,
    COL_DATE,
    COL_GENRE,
    COL_LENGTH,
    COL_PATH,
    COL_BITRATE,
) = range(9)


PREFS_DEFAULT_REPEAT_STATUS = False
PREFS_DEFAULT_COLUMNS_VISIBILITY = { COL_TRCK_NUM : True,
                                     COL_TITLE    : True,
                                     COL_ARTIST   : True,
                                     COL_ALBUM    : True,
                                     COL_DATE     : False,
                                     COL_GENRE    : False,
                                     COL_LENGTH   : True,
                                     COL_BITRATE  : False,
                                     COL_PATH     : False,
                                   }


class Tracklist(modules.Module):
    """ This module manages the tracklist """

    def __init__(self):
        """ Constructor """
        modules.Module.__init__(self, (consts.MSG_CMD_TRACKLIST_SET,     consts.MSG_CMD_TRACKLIST_CLR,     consts.MSG_CMD_TRACKLIST_ADD,
                                       consts.MSG_CMD_TOGGLE_PAUSE,      consts.MSG_CMD_NEXT,              consts.MSG_CMD_PREVIOUS,
                                       consts.MSG_EVT_NEED_BUFFER,       consts.MSG_EVT_STOPPED,           consts.MSG_EVT_PAUSED,
                                       consts.MSG_EVT_UNPAUSED,          consts.MSG_EVT_TRACK_ENDED_OK,    consts.MSG_EVT_TRACK_ENDED_ERROR,
                                       consts.MSG_CMD_TRACKLIST_SHUFFLE, consts.MSG_EVT_APP_STARTED,       consts.MSG_CMD_BRING_TO_FRONT,
                                       consts.MSG_CMD_TRACKLIST_DEL,     consts.MSG_CMD_TRACKLIST_REPEAT))


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
        self.btnClear.set_sensitive(False)
        self.btnShuffle.set_sensitive(False)
        # Create the list and its columns
        txtLRdr   = gtk.CellRendererText()
        txtRRdr   = gtk.CellRendererText()
        pixbufRdr = gtk.CellRendererPixbuf()
        txtRRdr.set_property('xalign', 1.0)

        # 'columns-visibility' may be broken, we should not use it (#311293)
        visible = tools.prefs.get(__name__, 'columns-visibility-2', PREFS_DEFAULT_COLUMNS_VISIBILITY)
        for (key, value) in PREFS_DEFAULT_COLUMNS_VISIBILITY.iteritems():
            if key not in visible:
                visible[key] = value

        columns = (('#',           [(pixbufRdr, gtk.gdk.Pixbuf), (txtRRdr, TYPE_INT)], (ROW_NUM, ROW_TIT),                            False, visible[COL_TRCK_NUM]),
                   (_('Title'),    [(txtLRdr, TYPE_STRING)],                           (ROW_TIT,),                                    True,  visible[COL_TITLE]),
                   (_('Artist'),   [(txtLRdr, TYPE_STRING)],                           (ROW_ART, ROW_ALB, ROW_NUM, ROW_TIT),          True,  visible[COL_ARTIST]),
                   (_('Album'),    [(txtLRdr, TYPE_STRING)],                           (ROW_ALB, ROW_NUM, ROW_TIT),                   True,  visible[COL_ALBUM]),
                   (_('Length'),   [(txtRRdr, TYPE_INT)],                              (ROW_LEN,),                                    False, visible[COL_LENGTH]),
                   (_('Bit Rate'), [(txtRRdr, TYPE_STRING)],                           (ROW_BTR, ROW_ART, ROW_ALB, ROW_NUM, ROW_TIT), False, visible[COL_BITRATE]),
                   (_('Genre'),    [(txtLRdr, TYPE_STRING)],                           (ROW_GNR, ROW_ART, ROW_ALB, ROW_NUM, ROW_TIT), False, visible[COL_GENRE]),
                   (_('Date'),     [(txtLRdr, TYPE_INT)],                              (ROW_DAT, ROW_ART, ROW_ALB, ROW_NUM, ROW_TIT), False, visible[COL_DATE]),
                   (_('Path'),     [(txtLRdr, TYPE_STRING)],                           (ROW_PTH,),                                    False, visible[COL_PATH]),
                   (None,          [(None, TYPE_PYOBJECT)],                            (None,),                                       False, False))

        self.list = ExtListView(columns, sortable=True, dndTargets=consts.DND_TARGETS.values(), useMarkup=False, canShowHideColumns=True)
        self.list.get_column(4).set_cell_data_func(txtRRdr, self.fmtLength)
        self.list.enableDNDReordering()
        wTree.get_widget('scrolled-tracklist').add(self.list)
        # GTK handlers
        self.list.connect('extlistview-dnd',                       self.onDND)
        self.list.connect('key-press-event',                       self.onKeyboard)
        self.list.connect('extlistview-modified',                  self.onListModified)
        self.list.connect('extlistview-button-pressed',            self.onButtonPressed)
        self.list.connect('extlistview-column-visibility-changed', self.onColumnVisibilityChanged)

        self.btnClear.connect('clicked',   lambda widget: modules.postMsg(consts.MSG_CMD_TRACKLIST_CLR))
        self.btnRepeat.connect('toggled',  self.onButtonRepeat)
        self.btnShuffle.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_TRACKLIST_SHUFFLE))
        # Restore preferences
        self.btnRepeat.set_active(tools.prefs.get(__name__, 'repeat-status', PREFS_DEFAULT_REPEAT_STATUS))
        # Set icons
        wTree.get_widget('img-repeat').set_from_icon_name('stock_repeat', gtk.ICON_SIZE_BUTTON)
        wTree.get_widget('img-shuffle').set_from_icon_name('stock_shuffle', gtk.ICON_SIZE_BUTTON)


    def getAllFiles(self):                  return [row[ROW_TRK].getFilePath() for row in self.list.iterAllRows()]
    def getAllTracks(self):                 return [row[ROW_TRK] for row in self.list.iterAllRows()]
    def fmtLength(self, col, cll, mdl, it): cll.set_property('text', tools.sec2str(mdl.get_value(it, ROW_LEN)))


    def __getNextTrackIdx(self):
        """ Return the index of the next track, or -1 if there is none """
        if self.list.hasMark():
            if self.list.getMark() < (len(self.list) - 1): return self.list.getMark() + 1
            elif self.btnRepeat.get_active():              return 0
        return -1


    def __getPreviousTrackIdx(self):
        """ Return the index of the previous track, or -1 if there is none """
        if self.list.hasMark():
            if self.list.getMark() > 0:       return self.list.getMark() - 1
            elif self.btnRepeat.get_active(): return len(self.list) - 1
        return -1


    def jumpToNext(self):
        """ Jump to the next track, if any """
        where = self.__getNextTrackIdx()
        if where != -1:
            self.jumpTo(where)


    def jumpToPrevious(self):
        """ Jump to the previous track, if any """
        where = self.__getPreviousTrackIdx()
        if where != -1:
            self.jumpTo(where)


    def jumpTo(self, trackIdx, sendPlayMsg = True):
        """ Jump to the track located at the given index """
        if self.list.hasMark() and self.list.getItem(self.list.getMark(), ROW_ICO) != icons.errorMenuIcon():
            self.list.setItem(self.list.getMark(), ROW_ICO, icons.nullMenuIcon())
        self.list.setMark(trackIdx)
        self.list.scroll_to_cell(trackIdx)
        self.list.setItem(trackIdx, ROW_ICO, icons.playMenuIcon())

        if sendPlayMsg:
            modules.postMsg(consts.MSG_CMD_PLAY, {'uri': self.list.getItem(trackIdx, ROW_TRK).getURI()})

        modules.postMsg(consts.MSG_EVT_NEW_TRACK,   {'track': self.list.getRow(trackIdx)[ROW_TRK]})
        modules.postMsg(consts.MSG_EVT_TRACK_MOVED, {'hasPrevious': self.__getPreviousTrackIdx() != -1, 'hasNext': self.__getNextTrackIdx() != -1})


    def onTrackEnded(self, withError):
        """ The current track has ended, jump to the next one if any """
        currIdx = self.list.getMark()

        # If an error occurred with the current track, flag it as such
        if withError:
            self.list.setItem(currIdx, ROW_ICO, icons.errorMenuIcon())

        # Find the next 'playable' track (not already flagged)
        if self.btnRepeat.get_active(): nbTracks = len(self.list)
        else:                           nbTracks = len(self.list) - 1 - currIdx

        for i in xrange(nbTracks):
            currIdx = (currIdx + 1) % len(self.list)

            if self.list.getItem(currIdx, ROW_ICO) != icons.errorMenuIcon():
                track = self.list.getItem(currIdx, ROW_TRK).getURI()
                self.jumpTo(currIdx, track != self.bufferedTrack)
                self.bufferedTrack = None
                return

        self.bufferedTrack = None
        modules.postMsg(consts.MSG_CMD_STOP)


    def onBufferingNeeded(self):
        """ The current track is close to its end, so we try to buffer the next one to avoid gaps """
        where = self.__getNextTrackIdx()
        if where != -1:
            self.bufferedTrack = self.list.getItem(where, ROW_TRK).getURI()
            modules.postMsg(consts.MSG_CMD_BUFFER, {'uri': self.bufferedTrack})


    def insert(self, tracks, playNow, position=None):
        """ Insert some tracks in the tracklist, append them if position is None """
        rows = [[icons.nullMenuIcon(), track.getNumber(), track.getTitle(), track.getArtist(), track.getExtendedAlbum(),
                    track.getLength(), track.getBitrate(), track.getGenre(), track.getDate(), track.getURI(), track] for track in tracks]

        if len(rows) != 0:
            self.previousTracklist = [row[ROW_TRK] for row in self.list.getAllRows()]

            for row in rows:
                self.playtime += row[ROW_LEN]

            self.list.insertRows(rows, position)

            if playNow:
                if position is not None: self.jumpTo(position)
                else:                    self.jumpTo(len(self.previousTracklist))


    def set(self, tracks, playNow):
        """ Replace the tracklist, clear it if tracks is None """
        self.playtime = 0

        # Save playlist only locally to this function
        # The insert() function would overwrite it otherwise
        previousTracklist = [row[ROW_TRK] for row in self.list.getAllRows()]

        if self.list.hasMark() and ((not playNow) or (tracks is None) or (len(tracks) == 0)):
            modules.postMsg(consts.MSG_CMD_STOP)

        self.list.clear()

        if tracks is not None and len(tracks) != 0:
            self.insert(tracks, playNow)

        self.previousTracklist = previousTracklist


    def onStopped(self):
        """ Playback has been stopped """
        if self.list.hasMark():
            currTrack = self.list.getMark()
            if self.list.getItem(currTrack, ROW_ICO) != icons.errorMenuIcon():
                self.list.setItem(currTrack, ROW_ICO, icons.nullMenuIcon())
            self.list.clearMark()


    def onPausedToggled(self, icon):
        """ Switch between paused and unpaused """
        if self.list.hasMark():
            self.list.setItem(self.list.getMark(), ROW_ICO, icon)


    def savePlaylist(self):
        """ Save the current tracklist to a playlist """
        outFile = gui.fileChooser.save(self.window, _('Save playlist'), 'playlist.m3u')

        if outFile is not None:
            media.playlist.save(self.getAllFiles(), outFile)


    def remove(self, idx=None):
        """ Remove the given track, or the selection if idx is None """
        if idx is not None and (idx < 0 or idx >= len(self.list)):
            return

        hadMark                = self.list.hasMark()
        self.previousTracklist = [row[ROW_TRK] for row in self.list.getAllRows()]

        if idx is not None:
            self.playtime -= self.list.getRow(idx)[ROW_LEN]
            self.list.removeRow((idx, ))
        else:
            self.playtime -= sum([row[ROW_LEN] for row in self.list.iterSelectedRows()])
            self.list.removeSelectedRows()

        self.list.unselectAll()

        if hadMark and not self.list.hasMark():
            modules.postMsg(consts.MSG_CMD_STOP)


    def crop(self):
        """ Remove the unselected tracks """
        hadMark                = self.list.hasMark()
        self.previousTracklist = [row[ROW_TRK] for row in self.list.getAllRows()]

        self.playtime = sum([row[ROW_LEN] for row in self.list.iterSelectedRows()])
        self.list.cropSelectedRows()

        if hadMark and not self.list.hasMark():
            modules.postMsg(consts.MSG_CMD_STOP)


    def revertTracklist(self):
        """ Back to the previous tracklist """
        self.set(self.previousTracklist, False)
        self.previousTracklist = None


    def shuffleTracklist(self):
        """ Shuffle the tracks and ensure that the current track stays visible """
        self.previousTracklist = [row[ROW_TRK] for row in self.list.getAllRows()]
        self.list.shuffle()
        if self.list.hasMark():
            self.list.scroll_to_cell(self.list.getMark())


    def setRepeat(self, repeat):
        """ Set/Unset the repeat function """
        if self.btnRepeat.get_active() != repeat:
            self.btnRepeat.clicked()


    def showPopupMenu(self, list, path, button, time):
        """ The index parameter may be None """
        popup = gtk.Menu()

        # Crop
        crop = gtk.ImageMenuItem(_('Crop'))
        crop.set_image(gtk.image_new_from_stock(gtk.STOCK_CUT, gtk.ICON_SIZE_MENU))
        crop.set_sensitive(path is not None)
        crop.connect('activate', lambda item: self.crop())
        popup.append(crop)

        # Remove
        remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        remove.set_sensitive(path is not None)
        remove.connect('activate', lambda item: self.remove())
        popup.append(remove)

        popup.append(gtk.SeparatorMenuItem())

        # Shuffle
        shuffle = gtk.ImageMenuItem(_('Shuffle Playlist'))
        shuffle.set_sensitive(len(list) != 0)
        shuffle.set_image(gtk.image_new_from_icon_name('stock_shuffle', gtk.ICON_SIZE_MENU))
        shuffle.connect('activate', lambda item: modules.postMsg(consts.MSG_CMD_TRACKLIST_SHUFFLE))
        popup.append(shuffle)

        # Revert
        revert = gtk.ImageMenuItem(_('Revert Playlist'))
        revert.set_image(gtk.image_new_from_stock(gtk.STOCK_REVERT_TO_SAVED, gtk.ICON_SIZE_MENU))
        revert.set_sensitive(self.previousTracklist is not None)
        revert.connect('activate', lambda item: self.revertTracklist())
        popup.append(revert)

        # Clear
        clear = gtk.ImageMenuItem(_('Clear Playlist'))
        clear.set_sensitive(len(list) != 0)
        clear.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_MENU))
        clear.connect('activate', lambda item: modules.postMsg(consts.MSG_CMD_TRACKLIST_CLR))
        popup.append(clear)

        popup.append(gtk.SeparatorMenuItem())

        # Repeat
        repeat = gtk.CheckMenuItem(_('Repeat'))
        repeat.set_active(tools.prefs.get(__name__, 'repeat-status', PREFS_DEFAULT_REPEAT_STATUS))
        repeat.connect('toggled', lambda item: self.btnRepeat.clicked())
        popup.append(repeat)

        popup.append(gtk.SeparatorMenuItem())

        # Save
        save = gtk.ImageMenuItem(_('Save Playlist As...'))
        save.set_sensitive(len(list) != 0)
        save.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE_AS, gtk.ICON_SIZE_MENU))
        save.connect('activate', lambda item: self.savePlaylist())
        popup.append(save)

        popup.show_all()
        popup.popup(None, None, None, button, time)


    # --== Message handler ==--


    def handleMsg(self, msg, params):
        """ A message has been received """
        if   msg == consts.MSG_EVT_PAUSED:                                   self.onPausedToggled(icons.pauseMenuIcon())
        elif msg == consts.MSG_EVT_STOPPED:                                  self.onStopped()
        elif msg == consts.MSG_EVT_UNPAUSED:                                 self.onPausedToggled(icons.playMenuIcon())
        elif msg == consts.MSG_EVT_APP_STARTED:                              self.onAppStarted()
        elif msg == consts.MSG_EVT_TRACK_ENDED_OK:                           self.onTrackEnded(False)
        elif msg == consts.MSG_EVT_TRACK_ENDED_ERROR:                        self.onTrackEnded(True)
        elif msg == consts.MSG_EVT_NEED_BUFFER:                              self.onBufferingNeeded()
        elif msg == consts.MSG_CMD_TRACKLIST_CLR:                            self.set(None, False)
        elif msg == consts.MSG_CMD_TRACKLIST_SET:                            self.set(params['tracks'], params['playNow'])
        elif msg == consts.MSG_CMD_TRACKLIST_ADD:                            self.insert(params['tracks'], params['playNow'])
        elif msg == consts.MSG_CMD_TRACKLIST_SHUFFLE:                        self.shuffleTracklist()
        elif msg == consts.MSG_CMD_PREVIOUS:                                 self.jumpToPrevious()
        elif msg == consts.MSG_CMD_NEXT:                                     self.jumpToNext()
        elif msg == consts.MSG_CMD_TRACKLIST_DEL:                            self.remove(params['idx'])
        elif msg == consts.MSG_CMD_BRING_TO_FRONT:                           self.window.present()
        elif msg == consts.MSG_CMD_TRACKLIST_REPEAT:                         self.setRepeat(params['repeat'])
        elif msg == consts.MSG_CMD_TOGGLE_PAUSE and not self.list.hasMark():
            if self.list.getSelectedRowsCount() != 0:
                self.jumpTo(self.list.getFirstSelectedRowIndex())
            else:
                self.jumpTo(0)


    # --== GTK handlers ==--


    def onButtonRepeat(self, btn):
        """ The 'repeat' button has been pressed """
        tools.prefs.set(__name__, 'repeat-status', self.btnRepeat.get_active())
        modules.postMsg(consts.MSG_EVT_REPEAT_CHANGED, {'repeat': self.btnRepeat.get_active()})
        if self.list.hasMark():
            modules.postMsg(consts.MSG_EVT_TRACK_MOVED, {'hasPrevious': self.__getPreviousTrackIdx() != -1, 'hasNext': self.__getNextTrackIdx() != -1})


    def onButtonPressed(self, list, event, path):
        """ Play the selected track on double click, or show a popup menu on right click """
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS and path is not None:
            self.jumpTo(path[0])
        elif event.button == 3:
            self.showPopupMenu(list, path, event.button, event.time)


    def onKeyboard(self, list, event):
        """ Keyboard shortcuts """
        keyname = gtk.gdk.keyval_name(event.keyval)

        if keyname == 'Delete':   self.remove()
        elif keyname == 'Return': self.jumpTo(self.list.getFirstSelectedRowIndex())
        elif keyname == 'space':  modules.postMsg(consts.MSG_CMD_TOGGLE_PAUSE)
        elif keyname == 'Escape': modules.postMsg(consts.MSG_CMD_STOP)
        elif keyname == 'Left':   modules.postMsg(consts.MSG_CMD_STEP, {'seconds': -5})
        elif keyname == 'Right':  modules.postMsg(consts.MSG_CMD_STEP, {'seconds': 5})


    def onListModified(self, list):
        """ Some rows have been added/removed/moved """
        self.btnClear.set_sensitive(len(list) != 0)
        self.btnShuffle.set_sensitive(len(list) != 0)

        # Update playlist length and playlist position for all tracks
        for position, row in enumerate(self.list.getAllRows()):
            row[ROW_TRK].setPlaylistPos(position + 1)
            row[ROW_TRK].setPlaylistLen(len(self.list))

        modules.postMsg(consts.MSG_EVT_NEW_TRACKLIST, {'tracks': self.getAllTracks(), 'playtime': self.playtime})

        if self.list.hasMark():
            modules.postMsg(consts.MSG_EVT_TRACK_MOVED, {'hasPrevious': self.__getPreviousTrackIdx() != -1, 'hasNext':  self.__getNextTrackIdx() != -1})


    def onColumnVisibilityChanged(self, list, colTitle, visible):
        """ A column has been shown/hidden """
        if colTitle == '#':             colId = COL_TRCK_NUM
        elif colTitle == _('Title'):    colId = COL_TITLE
        elif colTitle == _('Artist'):   colId = COL_ARTIST
        elif colTitle == _('Album'):    colId = COL_ALBUM
        elif colTitle == _('Length'):   colId = COL_LENGTH
        elif colTitle == _('Genre'):    colId = COL_GENRE
        elif colTitle == _('Date'):     colId = COL_DATE
        elif colTitle == _('Bit Rate'): colId = COL_BITRATE
        else:                           colId = COL_PATH

        visibility = tools.prefs.get(__name__, 'columns-visibility-2', PREFS_DEFAULT_COLUMNS_VISIBILITY)
        visibility[colId] = visible
        tools.prefs.set(__name__, 'columns-visibility-2', visibility)


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

        dropInfo = list.get_dest_row_at_pos(x, y)

        # Insert the tracks, but beware of the AFTER/BEFORE mechanism used by GTK
        if dropInfo is None:                          self.insert(tracks, False)
        elif dropInfo[1] == gtk.TREE_VIEW_DROP_AFTER: self.insert(tracks, False, dropInfo[0][0] + 1)
        else:                                         self.insert(tracks, False, dropInfo[0][0])

        context.finish(True, False, time)
