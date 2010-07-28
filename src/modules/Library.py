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

import gtk, media, modules, os, tools

from tools                 import consts, htmlEscape, icons, prefs, pickleLoad, pickleSave
from gettext               import ngettext, gettext as _
from os.path               import isdir, isfile
from gobject               import idle_add, TYPE_STRING, TYPE_INT, TYPE_PYOBJECT
from tools.log             import logger
from media.track.fileTrack import FileTrack

MOD_INFO = ('Library', _('Library'), _('Organize your music by tags'), [], False, True)
MOD_L10N = MOD_INFO[modules.MODINFO_L10N]


# Information associated with libraries
(
    LIB_PATH,        # Physical location of media files
    LIB_NB_ARTISTS,  # Number of artists
    LIB_NB_ALBUMS,   # Number of albums
    LIB_NB_TRACKS    # Number of tracks
) = range(4)


# Information associated with artists
(
    ART_NAME,       # Its name
    ART_INDEX,      # Name of the directory: avoid the use of the artist name as a filename (may contain invalid characters)
    ART_NB_ALBUMS   # How many albums
) = range(3)


# Information associated with albums
(
    ALB_NAME,       # Its name
    ALB_INDEX,      # Name of the file: avoid the use of the artist name as a filename (may contain invalid characters)
    ALB_NB_TRACKS,  # Number of tracks
    ALB_LENGTH      # Complete duration (include all tracks)
) = range(4)


# Possible types for a node of the tree
(
    TYPE_ARTIST,            # Artist
    TYPE_ALBUM,             # Album
    TYPE_TRACK,             # Single track
    TYPE_HEADER,            # Alphabetical header
    TYPE_FAVORITES_BANNER,  # Favorites banner (when showing only favorites)
    TYPE_NONE               # Used for fake children
) = range(6)


# The format of a row in the treeview
(
    ROW_PIXBUF,    # Item icon
    ROW_ALBUM_LEN, # Length of the album (invisible when not an album)
    ROW_NAME,      # Item name
    ROW_TYPE,      # The type of the item (e.g., directory, file)
    ROW_FULLPATH,  # The full path to the item
    ROW_DATA       # Arbitrary data that depend on the type of the row
) = range(6)


# Constants
VERSION                           = 3                                      # Used to check compatibility
ROOT_PATH                         = os.path.join(consts.dirCfg, 'Library') # Path where libraries are stored
FAKE_CHILD                        = (None, None, '', TYPE_NONE, '', None)  # We use a lazy tree
PREFS_DEFAULT_PREFIXES            = {'the ': None}                         # Prefixes are put at the end of artists' names
PREFS_DEFAULT_LIBRARIES           = {}                                     # No libraries at first
PREFS_DEFAULT_TREE_STATE          = {}                                     # No state at first
PREFS_DEFAULT_SHOW_ONLY_FAVORITES = False


class Library(modules.Module):


    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_APP_QUIT:         self.onModUnloaded,
                        consts.MSG_EVT_MOD_LOADED:       self.onModLoaded,
                        consts.MSG_EVT_APP_STARTED:      self.onModLoaded,
                        consts.MSG_EVT_MOD_UNLOADED:     self.onModUnloaded,
                        consts.MSG_EVT_EXPLORER_CHANGED: self.onExplorerChanged,
                   }

        modules.Module.__init__(self, handlers)


    def __createTree(self):
        """ Create the main tree, add it to the scrolled window """
        from gui.extTreeview import ExtTreeView

        txtRdr         = gtk.CellRendererText()
        pixbufRdr      = gtk.CellRendererPixbuf()
        txtRdrAlbumLen = gtk.CellRendererText()

        columns = (('',   [(pixbufRdr, gtk.gdk.Pixbuf), (txtRdrAlbumLen, TYPE_STRING), (txtRdr, TYPE_STRING)], False),
                   (None, [(None, TYPE_INT)],                                                                  False),
                   (None, [(None, TYPE_STRING)],                                                               False),
                   (None, [(None, TYPE_PYOBJECT)],                                                             False))

        self.tree = ExtTreeView(columns, True)

        # The first text column (ROW_ALBUM_LEN) is not the one to search for
        # set_search_column(ROW_NAME) should work, but it doesn't...
        self.tree.set_search_equal_func(self.__searchFunc)

        self.tree.get_column(0).set_cell_data_func(txtRdr,         self.__drawCell)
        self.tree.get_column(0).set_cell_data_func(pixbufRdr,      self.__drawCell)
        self.tree.get_column(0).set_cell_data_func(txtRdrAlbumLen, self.__drawAlbumLenCell)

        # The album length is written in a smaller font, with a lighter color
        txtRdrAlbumLen.set_property('scale', 0.85)
        txtRdrAlbumLen.set_property('foreground', '#909090')

        self.tree.setDNDSources([consts.DND_TARGETS[consts.DND_DAP_TRACKS]])
        # GTK handlers
        self.tree.connect('drag-data-get',              self.onDragDataGet)
        self.tree.connect('key-press-event',            self.onKeyPressed)
        self.tree.connect('exttreeview-row-expanded',   self.onRowExpanded)
        self.tree.connect('exttreeview-row-collapsed',  self.onRowCollapsed)
        self.tree.connect('exttreeview-button-pressed', self.onButtonPressed)
        # Add the tree to the scrolled window
        self.scrolled.add(self.tree)


    def __searchFunc(self, model, column, key, iter):
        """ Check whether the given key matches the current candidate (iter) """
        return model.get_value(iter, ROW_NAME)[:len(key)].lower() != key.lower()


    def __drawCell(self, column, cell, model, iter):
        """ Use a different background color for alphabetical headers """
        if model.get_value(iter, ROW_TYPE) == TYPE_HEADER: cell.set_property('cell-background-gdk', self.tree.style.bg[gtk.STATE_PRELIGHT])
        else:                                              cell.set_property('cell-background',     None)


    def __drawAlbumLenCell(self, column, cell, model, iter):
        """ Use a different background color for alphabetical headers """
        if model.get_value(iter, ROW_ALBUM_LEN) is None: cell.set_property('visible', False)
        else:                                            cell.set_property('visible', True)


    def __createEmptyLibrary(self, name):
        """ Create bootstrap files for a new library """
        import shutil

        # Make sure that the root directory of all libraries exists
        if not isdir(ROOT_PATH):
            os.mkdir(ROOT_PATH)
        # Start from an empty library
        libPath = os.path.join(ROOT_PATH, name)
        if isdir(libPath):
            shutil.rmtree(libPath)
        os.mkdir(libPath)
        pickleSave(os.path.join(libPath, 'files'), {})


    def refreshLibrary(self, parent, libName, path, creation=False):
        """ Refresh the given library, must be called through idle_add() """
        import collections, shutil

        from gui import progressDlg

        # First show a progress dialog
        if creation: header = _('Creating library')
        else:        header = _('Refreshing library')

        progress = progressDlg.ProgressDlg(parent, header, _('The directory is scanned for media files. This can take some time.\nPlease wait.'))
        yield True

        libPath = os.path.join(ROOT_PATH, libName)   # Location of the library

        # If the version number has changed or does not exist, don't reuse any existing file and start from scratch
        if not os.path.exists(os.path.join(libPath, 'VERSION_%u' % VERSION)):
            self.__createEmptyLibrary(libName)

        db         = {}                                                                # The dictionnary used to create the library
        queue      = collections.deque((path,))                                        # Faster structure for appending/removing elements
        mediaFiles = []                                                                # All media files found
        newLibrary = {}                                                                # Reflect the current file structure of the library
        oldLibrary = pickleLoad(os.path.join(libPath, 'files'))                        # Previous file structure of the same library

        # Make sure the root directory still exists
        if not os.path.exists(path):
            queue.pop()

        while len(queue) != 0:
            currDir      = queue.pop()
            currDirMTime = os.stat(currDir).st_mtime

            # Retrieve previous information on the current directory, if any
            if currDir in oldLibrary: oldDirMTime, oldDirectories, oldFiles = oldLibrary[currDir]
            else:                     oldDirMTime, oldDirectories, oldFiles = -1, [], {}

            # If the directory has not been modified, keep old information
            if currDirMTime == oldDirMTime:
                files, directories = oldFiles, oldDirectories
            else:
                files, directories = {}, []
                for (filename, fullPath) in tools.listDir(currDir):
                    if isdir(fullPath):
                        directories.append(fullPath)
                    elif isfile(fullPath) and media.isSupported(filename):
                        if filename in oldFiles: files[filename] = oldFiles[filename]
                        else:                    files[filename] = [-1, FileTrack(fullPath)]

            # Determine which files need to be updated
            for filename, (oldMTime, track) in files.iteritems():
                mTime = os.stat(track.getFilePath()).st_mtime
                if mTime != oldMTime:
                    files[filename] = [mTime, media.getTrackFromFile(track.getFilePath())]

            newLibrary[currDir] = (currDirMTime, directories, files)
            mediaFiles.extend([track for mTime, track in files.itervalues()])
            queue.extend(directories)

            # Update the progress dialog
            try:
                text = ngettext('Scanning directories (one track found)', 'Scanning directories (%(nbtracks)u tracks found)', len(mediaFiles))
                progress.pulse(text % {'nbtracks': len(mediaFiles)})
                yield True
            except progressDlg.CancelledException:
                progress.destroy()
                if creation:
                    shutil.rmtree(libPath)
                yield False

        # From now on, the process should not be cancelled
        progress.setCancellable(False)
        if creation: progress.pulse(_('Creating library...'))
        else:        progress.pulse(_('Refreshing library...'))
        yield True

        # Create the database
        for track in mediaFiles:
            album = track.getExtendedAlbum()

            if track.hasAlbumArtist(): artist = track.getAlbumArtist()
            else:                      artist = track.getArtist()

            if artist in db:
                allAlbums = db[artist]
                if album in allAlbums: allAlbums[album].append(track)
                else:                  allAlbums[album] = [track]
            else:
                db[artist] = {album: [track]}

        progress.pulse()
        yield True

        # If an artist name begins with a known prefix, put it at the end (e.g., Future Sound of London (The))
        prefixes = prefs.get(__name__, 'prefixes', PREFS_DEFAULT_PREFIXES)
        for artist in db.keys():
            artistLower = artist.lower()
            for prefix in prefixes:
                if artistLower.startswith(prefix):
                    db[artist[len(prefix):] + ' (%s)' % artist[:len(prefix)-1]] = db[artist]
                    del db[artist]

        progress.pulse()
        yield True

        # Load favorites before removing the files from the disk
        if self.currLib == libName: favorites = self.favorites
        else:                       favorites = self.loadFavorites(libName)

        # Re-create the library structure on the disk
        if isdir(libPath):
            shutil.rmtree(libPath)
            os.mkdir(libPath)

        # Put a version number
        tools.touch(os.path.join(libPath, 'VERSION_%u' % VERSION))

        overallNbAlbums  = 0
        overallNbTracks  = 0
        overallNbArtists = len(db)

        # The 'artists' file contains all known artists with their index, the 'files' file contains the file structure of the root path
        allArtists = sorted([(artist, str(indexArtist), len(db[artist])) for indexArtist, artist in enumerate(db)], key = lambda a: a[0].lower())
        pickleSave(os.path.join(libPath, 'files'),   newLibrary)
        pickleSave(os.path.join(libPath, 'artists'), allArtists)

        for (artist, indexArtist, nbAlbums) in allArtists:
            artistPath       = os.path.join(libPath, indexArtist)
            overallNbAlbums += nbAlbums
            os.mkdir(artistPath)

            albums = []
            for index, (name, tracks) in enumerate(db[artist].iteritems()):
                length           = sum([track.getLength() for track in tracks])
                overallNbTracks += len(tracks)

                albums.append((name, str(index), len(tracks), length))
                pickleSave(os.path.join(artistPath, str(index)), sorted(tracks, key = lambda track: track.getNumber()))

            albums.sort(cmp = lambda a1, a2: cmp(db[artist][a1[0]][0], db[artist][a2[0]][0]))
            pickleSave(os.path.join(artistPath, 'albums'), albums)
            progress.pulse()
            yield True

        self.libraries[libName] = (path, overallNbArtists, overallNbAlbums, overallNbTracks)
        self.fillLibraryList()
        if creation:
            modules.postMsg(consts.MSG_CMD_EXPLORER_ADD, {'modName': MOD_L10N, 'expName': libName, 'icon': None, 'widget': self.scrolled})
        progress.destroy()

        # Trim favorites and save them
        newFavorites = {}
        for (artist, albums) in favorites.iteritems():
            if artist in db:
                newFavorites[artist] = {}
                for album in albums:
                    if album in db[artist]:
                        newFavorites[artist][album] = None

        self.saveFavorites(libName, newFavorites)

        # If the refreshed library is currently displayed, refresh the treeview as well
        if self.currLib == libName:
            self.saveTreeState()
            self.favorites = newFavorites
            self.loadArtists(self.tree, self.currLib)
            self.restoreTreeState()

        yield False


    def __getTracksFromPaths(self, tree, paths):
        """
            Return the list of tracks extracted from:
                * The list 'paths' if it is not None
                * The currently selected rows if 'paths' is None
        """
        from sys import maxint

        tracks = []

        if paths is None:
            paths = tree.getSelectedPaths()

        for currPath in paths:
            row = tree.getRow(currPath)
            if row[ROW_TYPE] == TYPE_TRACK:
                tracks.append(row[ROW_DATA])
            elif row[ROW_TYPE] == TYPE_ALBUM:
                tracks.extend(pickleLoad(row[ROW_FULLPATH]))
            elif row[ROW_TYPE] == TYPE_ARTIST:
                for album in pickleLoad(os.path.join(row[ROW_FULLPATH], 'albums')):
                    tracks.extend(pickleLoad(os.path.join(row[ROW_FULLPATH], album[ALB_INDEX])))
            elif row[ROW_TYPE] == TYPE_HEADER:
                for path in xrange(currPath[0]+1, maxint):
                    if not tree.isValidPath(path):
                        break

                    row = tree.getRow(path)
                    if row[ROW_TYPE] == TYPE_HEADER:
                        break

                    for album in pickleLoad(os.path.join(row[ROW_FULLPATH], 'albums')):
                        tracks.extend(pickleLoad(os.path.join(row[ROW_FULLPATH], album[ALB_INDEX])))

        return tracks


    def playPaths(self, tree, paths, replace):
        """
            Replace/extend the tracklist
            If the list 'paths' is None, use the current selection
        """
        tracks = self.__getTracksFromPaths(tree, paths)

        if replace: modules.postMsg(consts.MSG_CMD_TRACKLIST_SET, {'tracks': tracks, 'playNow': True})
        else:       modules.postMsg(consts.MSG_CMD_TRACKLIST_ADD, {'tracks': tracks, 'playNow': False})


    def pickAlbumArtist(self, tree, artistPath):
        """ Pick an album at random of the given artist and play it """
        import random

        # Expanding the artist row populates it, so that we can then pick an album at random
        tree.expandRow(artistPath)
        albumPath = artistPath + (random.randint(0, tree.getNbChildren(artistPath)-1), )

        # Select the random album and play it
        tree.get_selection().unselect_all()
        tree.get_selection().select_path(albumPath)
        tree.scroll(albumPath)
        self.playPaths(tree, [albumPath], True)


    def pickAlbumLibrary(self, tree):
        """ Pick an album at random in the library and play it """
        import random

        # Pick an artist at random (make sure not to select an alphabetical header)
        path = (random.randint(0, tree.getCount()-1), )
        while tree.getItem(path, ROW_TYPE) != TYPE_ARTIST:
            path = (random.randint(0, tree.getCount()-1), )

        self.pickAlbumArtist(tree, path)


    def switchFavoriteStateOfSelectedItems(self, tree):
        """ Add to/remove from favorites the selected items """
        # Go through selected items and switch their state
        removed = False
        for path in tree.getSelectedPaths():
            if tree.getItem(path, ROW_TYPE) == TYPE_ALBUM:
                album  = tree.getItem(path, ROW_DATA)
                artist = tree.getItem(path[:-1], ROW_DATA)

                if self.isAlbumInFavorites(artist, album):
                    removed = True
                    tree.setItem(path, ROW_PIXBUF, icons.mediaDirMenuIcon())
                    self.removeFromFavorites(artist, album)
                else:
                    tree.setItem(path, ROW_PIXBUF, icons.starDirMenuIcon())
                    self.addToFavorites(artist, album)

        # If some favorites were removed, we may have to reload the tree
        if self.showOnlyFavorites and removed:
            self.saveTreeState()
            self.loadArtists(self.tree, self.currLib)
            self.restoreTreeState()


    def switchFavoritesView(self, tree):
        """ Show all/favorites """
        self.saveTreeState()
        self.showOnlyFavorites = not self.showOnlyFavorites
        prefs.set(__name__, 'show-only-favorites', self.showOnlyFavorites)
        self.loadArtists(self.tree, self.currLib)
        self.restoreTreeState()


    def showPopupMenu(self, tree, button, time, path):
        """ Show a popup menu """
        popup = gtk.Menu()

        # Play
        play = gtk.ImageMenuItem(gtk.STOCK_MEDIA_PLAY)
        popup.append(play)

        if path is None: play.set_sensitive(False)
        else:            play.connect('activate', lambda widget: self.playPaths(tree, None, True))

        # Separator
        popup.append(gtk.SeparatorMenuItem())

        # Add to/remove from favorites
        favCpt    = 0
        nonFavCpt = 0
        for node in tree.getSelectedPaths():
            if tree.getItem(node, ROW_TYPE) != TYPE_ALBUM:
                favCpt    = 1
                nonFavCpt = 1
                break
            elif tree.getItem(node, ROW_PIXBUF) == icons.mediaDirMenuIcon():
                nonFavCpt += 1
            else:
                favCpt += 1

        if favCpt == 0:      favorite = gtk.ImageMenuItem(_('Add to Favorites'))
        elif nonFavCpt == 0: favorite = gtk.ImageMenuItem(_('Remove from Favorites'))
        else:                favorite = gtk.ImageMenuItem(_('Favorites'))

        favorite.get_image().set_from_pixbuf(icons.starMenuIcon())
        popup.append(favorite)

        if TYPE_ALBUM in [tree.getItem(path, ROW_TYPE) for path in tree.getSelectedPaths()]:
            favorite.connect('activate', lambda widget: self.switchFavoriteStateOfSelectedItems(tree))
        else:
            favorite.set_sensitive(False)

        # Show only favorites
        showFavorites = gtk.CheckMenuItem(_('Show Only Favorites'))
        showFavorites.set_active(self.showOnlyFavorites)
        showFavorites.connect('toggled', lambda widget: self.switchFavoritesView(tree))
        popup.append(showFavorites)

        # Separator
        popup.append(gtk.SeparatorMenuItem())

        # Collapse all nodes
        collapse = gtk.ImageMenuItem(_('Collapse all'))
        collapse.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_MENU))
        popup.append(collapse)

        enabled = False
        for child in self.tree.iterChildren(None):
            if self.tree.row_expanded(child):
                enabled = True
                break

        if enabled: collapse.connect('activate', lambda widget: self.tree.collapse_all())
        else:       collapse.set_sensitive(False)

        # Refresh the library
        refresh = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        refresh.connect('activate', lambda widget: idle_add(self.refreshLibrary(None, self.currLib, self.libraries[self.currLib][LIB_PATH]).next))
        popup.append(refresh)

        # Randomness
        randomness     = gtk.Menu()
        randomnessItem = gtk.ImageMenuItem(_('Randomness'))
        randomnessItem.get_image().set_from_icon_name('stock_shuffle', gtk.ICON_SIZE_MENU)
        randomnessItem.set_submenu(randomness)
        popup.append(randomnessItem)

        # Random album of the selected artist
        if path is not None and tree.getItem(path, ROW_TYPE) == TYPE_ARTIST:
            album = gtk.MenuItem(_('Pick an album of %(artist)s' % {'artist': tree.getItem(path, ROW_NAME).replace('&amp;', '&')}))
            album.connect('activate', lambda widget: self.pickAlbumArtist(tree, path))
            randomness.append(album)

        # Random album in the entire library
        album = gtk.MenuItem(_('Pick an album in the library'))
        album.connect('activate', lambda widget: self.pickAlbumLibrary(tree))
        randomness.append(album)

        popup.show_all()
        popup.popup(None, None, None, button, time)


    # --== Populating the tree ==--


    def loadArtists(self, tree, name):
        """ Load the given library """
        libPath = os.path.join(ROOT_PATH, name)

        # Make sure the version number is the good one
        if not os.path.exists(os.path.join(libPath, 'VERSION_%u' % VERSION)):
            logger.error('[%s] Version number does not match, loading of library "%s" aborted' % (MOD_INFO[modules.MODINFO_NAME], name))
            error = _('This library is deprecated, please refresh it.')
            tree.replaceContent([(icons.errorMenuIcon(), None, error, TYPE_NONE, None, None)])
            return

        rows       = []
        icon       = icons.dirMenuIcon()
        prevChar   = ''
        allArtists = pickleLoad(os.path.join(libPath, 'artists'))

        # Filter artists if needed
        if self.showOnlyFavorites:
            allArtists = [artist for artist in allArtists if self.isArtistInFavorites(artist[ART_NAME])]
            rows.append((icons.starMenuIcon(), None, '<b>%s</b>' % _('My Favorites'), TYPE_FAVORITES_BANNER, None, None))

        # Create the rows
        for artist in allArtists:
            if len(artist[ART_NAME]) != 0: currChar = unicode(artist[ART_NAME], errors='replace')[0].lower()
            else:                          currChar = prevChar

            if prevChar != currChar and not (prevChar.isdigit() and currChar.isdigit()):
                prevChar = currChar
                if currChar.isdigit(): rows.append((None, None, '<b>0 - 9</b>',                 TYPE_HEADER, None, None))
                else:                  rows.append((None, None, '<b>%s</b>' % currChar.upper(), TYPE_HEADER, None, None))

            rows.append((icon, None, htmlEscape(artist[ART_NAME]), TYPE_ARTIST, os.path.join(libPath, artist[ART_INDEX]), artist[ART_NAME]))

        # Insert all rows, and then add a fake child to each artist
        tree.replaceContent(rows)
        for node in tree.iterChildren(None):
            if tree.getItem(node, ROW_TYPE) == TYPE_ARTIST:
                tree.appendRow(FAKE_CHILD, node)


    def loadAlbums(self, tree, node, fakeChild):
        """ Initial load of the albums of the given node, assuming it is of type TYPE_ARTIST """
        rows      = []
        path      = tree.getItem(node, ROW_FULLPATH)
        artist    = tree.getItem(node, ROW_DATA)
        allAlbums = pickleLoad(os.path.join(tree.getItem(node, ROW_FULLPATH), 'albums'))

        # Filter albums if only favorites should be shown
        if self.showOnlyFavorites:
            allAlbums = [album for album in allAlbums if self.isAlbumInFavorites(artist, album[ALB_NAME])]

        # The icon depends on whether the album is in the favorites
        for album in allAlbums:
            if self.isAlbumInFavorites(artist, album[ALB_NAME]): icon = icons.starDirMenuIcon()
            else:                                                icon = icons.mediaDirMenuIcon()

            rows.append((icon, '[%s]' % tools.sec2str(album[ALB_LENGTH], True), '%s' % htmlEscape(album[ALB_NAME]),
                            TYPE_ALBUM, os.path.join(path, album[ALB_INDEX]), album[ALB_NAME]))

        # Add all the rows, and then add a fake child to each of them
        tree.appendRows(rows, node)
        tree.removeRow(fakeChild)
        for child in tree.iterChildren(node):
            tree.appendRow(FAKE_CHILD, child)


    def loadTracks(self, tree, node, fakeChild):
        """ Initial load of all tracks of the given node, assuming it is of type TYPE_ALBUM """
        allTracks = pickleLoad(tree.getItem(node, ROW_FULLPATH))
        icon      = icons.mediaFileMenuIcon()
        rows      = [(icon, None, '%02u. %s' % (track.getNumber(), htmlEscape(track.getTitle())), TYPE_TRACK, track.getFilePath(), track) for track in allTracks]

        tree.appendRows(rows, node)
        tree.removeRow(fakeChild)


    # --== Manage tree state ==--


    def saveTreeState(self):
        """ Save the current tree state """
        if self.showOnlyFavorites: self.treeState[self.currLib + ' favorites'] = self.tree.saveState(ROW_NAME)
        else:                      self.treeState[self.currLib]                = self.tree.saveState(ROW_NAME)


    def restoreTreeState(self):
        """ Restore the tree state """
        if self.showOnlyFavorites: name = self.currLib + ' favorites'
        else:                      name = self.currLib

        if name in self.treeState:
            self.tree.restoreState(self.treeState[name], ROW_NAME)


    def removeTreeStates(self, libName):
        """ Remove the tree states associated to the given library """
        if libName in self.treeState:                del self.treeState[libName]
        if libName + ' favorites' in self.treeState: del self.treeState[libName + ' favorites']


    def renameTreeStates(self, oldLibName, newLibName):
        """ Rename the tree states associated with oldLibName """
        if oldLibName in self.treeState:
            self.treeState[newLibName] = self.treeState[oldLibName]
            del self.treeState[oldLibName]

        if oldLibName + ' favorites' in self.treeState:
            self.treeState[newLibName + ' favorites'] = self.treeState[oldLibName + ' favorites']
            del self.treeState[oldLibName + ' favorites']


    # --== Favorites ==--


    def loadFavorites(self, libName):
        """ Load favorites from the disk """
        try:    return pickleLoad(os.path.join(ROOT_PATH, libName, 'favorites'))
        except: return {}


    def saveFavorites(self, libName, favorites):
        """ Save favorites to the disk """
        pickleSave(os.path.join(ROOT_PATH, libName, 'favorites'), favorites)


    def isArtistInFavorites(self, artist):
        """ Return whether the given artist is in the favorites (at least one album) """
        return artist in self.favorites


    def isAlbumInFavorites(self, artist, album):
        """ Return whether the given album is in the favorites """
        return artist in self.favorites and album in self.favorites[artist]


    def addToFavorites(self, artist, album):
        """ Add the given album to the favorites """
        if artist in self.favorites: self.favorites[artist][album] = None
        else:                        self.favorites[artist] = {album: None}


    def removeFromFavorites(self, artist, album):
        """ Remove the given album from the favorites """
        del self.favorites[artist][album]

        if len(self.favorites[artist]) == 0:
            del self.favorites[artist]


    # --== GTK handlers ==--


    def onRowExpanded(self, tree, node):
        """ Populate the expanded row """
        if tree.getItem(node, ROW_TYPE) == TYPE_ARTIST: self.loadAlbums(tree, node, tree.getChild(node, 0))
        else:                                           self.loadTracks(tree, node, tree.getChild(node, 0))


    def onRowCollapsed(self, tree, node):
        """ Replace all children of the node by a fake child """
        tree.removeAllChildren(node)
        tree.appendRow(FAKE_CHILD, node)


    def onButtonPressed(self, tree, event, path):
        """ A mouse button has been pressed """
        if event.button == 3:
            self.showPopupMenu(tree, event.button, event.time, path)
        elif path is not None and tree.getItem(path, ROW_TYPE) != TYPE_NONE:
            if event.button == 2:
                self.playPaths(tree, [path], False)
            elif event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                if   tree.getItem(path, ROW_PIXBUF) != icons.dirMenuIcon(): self.playPaths(tree, None, True)
                elif tree.row_expanded(path):                               tree.collapse_row(path)
                else:                                                       tree.expand_row(path, False)


    def onKeyPressed(self, tree, event):
        """ A key has been pressed """
        keyname = gtk.gdk.keyval_name(event.keyval)

        if   keyname == 'F5':     idle_add(self.refreshLibrary(None, self.currLib, self.libraries[self.currLib][LIB_PATH]).next)
        elif keyname == 'plus':   tree.expandRows()
        elif keyname == 'Left':   tree.collapseRows()
        elif keyname == 'Right':  tree.expandRows()
        elif keyname == 'minus':  tree.collapseRows()
        elif keyname == 'space':  tree.switchRows()
        elif keyname == 'Return': self.playPaths(tree, None, True)


    def onDragDataGet(self, tree, context, selection, info, time):
        """ Provide information about the data being dragged """
        serializedTracks = '\n'.join([track.serialize() for track in self.__getTracksFromPaths(tree, None)])
        selection.set(consts.DND_TARGETS[consts.DND_DAP_TRACKS][0], 8, serializedTracks)


    def addAllExplorers(self):
        """ Add all libraries to the Explorer module """
        for (name, (path, nbArtists, nbAlbums, nbTracks)) in self.libraries.iteritems():
            modules.postMsg(consts.MSG_CMD_EXPLORER_ADD, {'modName': MOD_L10N, 'expName': name, 'icon': None, 'widget': self.scrolled})


    def removeAllExplorers(self):
        """ Remove all libraries from the Explorer module """
        for (name, (path, nbArtists, nbAlbums, nbTracks)) in self.libraries.iteritems():
            modules.postMsg(consts.MSG_CMD_EXPLORER_REMOVE, {'modName': MOD_L10N, 'expName': name})


   # --== Message handlers ==--


    def onModLoaded(self):
        """ This is the real initialization function, called when the module has been loaded """
        self.tree              = None
        self.currLib           = None
        self.cfgWindow         = None
        self.libraries         = prefs.get(__name__, 'libraries',  PREFS_DEFAULT_LIBRARIES)
        self.treeState         = prefs.get(__name__, 'tree-state', PREFS_DEFAULT_TREE_STATE)
        self.favorites         = None
        self.showOnlyFavorites = prefs.get(__name__, 'show-only-favorites', PREFS_DEFAULT_SHOW_ONLY_FAVORITES)
        # Scroll window
        self.scrolled = gtk.ScrolledWindow()
        self.scrolled.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled.show()

        idle_add(self.addAllExplorers)


    def onModUnloaded(self):
        """ The module has been unloaded """
        if self.currLib is not None:
            self.saveTreeState()
            self.saveFavorites(self.currLib, self.favorites)
            prefs.set(__name__, 'tree-state', self.treeState)

        prefs.set(__name__, 'libraries',  self.libraries)
        self.removeAllExplorers()


    def onExplorerChanged(self, modName, expName):
        """ A new explorer has been selected """
        if modName == MOD_L10N and expName != self.currLib:
            # Create the tree if needed
            if self.tree is None:
                self.__createTree()

            # Save the state of the current library
            if self.currLib is not None:
                self.saveTreeState()
                self.saveFavorites(self.currLib, self.favorites)

            # Switch to the new library
            self.currLib   = expName
            self.favorites = self.loadFavorites(self.currLib)
            self.loadArtists(self.tree, self.currLib)
            self.restoreTreeState()


    # --== Configuration ==--


    def configure(self, parent):
        """ Show the configuration dialog """
        if self.cfgWindow is None:
            from gui import extListview, window

            self.cfgWindow = window.Window('Library.glade', 'vbox1', __name__, MOD_L10N, 370, 400)
            # Create the list of libraries
            txtRdr  = gtk.CellRendererText()
            pixRdr  = gtk.CellRendererPixbuf()
            columns = ((None, [(txtRdr, TYPE_STRING)],                           0, False, False),
                       ('',   [(pixRdr, gtk.gdk.Pixbuf), (txtRdr, TYPE_STRING)], 2, False, True))

            self.cfgList = extListview.ExtListView(columns, sortable=False, useMarkup=True, canShowHideColumns=False)
            self.cfgList.set_headers_visible(False)
            self.cfgWindow.getWidget('scrolledwindow1').add(self.cfgList)
            # Connect handlers
            self.cfgList.connect('key-press-event', self.onCfgKeyboard)
            self.cfgList.get_selection().connect('changed', self.onCfgSelectionChanged)
            self.cfgWindow.getWidget('btn-add').connect('clicked', self.onAddLibrary)
            self.cfgWindow.getWidget('btn-rename').connect('clicked', self.onRenameLibrary)
            self.cfgWindow.getWidget('btn-remove').connect('clicked', lambda btn: self.removeSelectedLibraries(self.cfgList))
            self.cfgWindow.getWidget('btn-refresh').connect('clicked', self.onRefresh)
            self.cfgWindow.getWidget('btn-ok').connect('clicked', lambda btn: self.cfgWindow.hide())
            self.cfgWindow.getWidget('btn-cancel').connect('clicked', lambda btn: self.cfgWindow.hide())
            self.cfgWindow.getWidget('btn-help').connect('clicked', self.onHelp)

        if not self.cfgWindow.isVisible():
            self.fillLibraryList()
            self.cfgWindow.getWidget('btn-ok').grab_focus()

        self.cfgWindow.show()


    def onRefresh(self, btn):
        """ Refresh the first selected library """
        name = self.cfgList.getSelectedRows()[0][0]
        idle_add(self.refreshLibrary(self.cfgWindow, name, self.libraries[name][LIB_PATH]).next)


    def onAddLibrary(self, btn):
        """ Let the user create a new library """
        from gui.selectPath import SelectPath

        result = SelectPath(MOD_L10N, self.cfgWindow, self.libraries.keys(), ['/']).run()

        if result is not None:
            name, path = result
            idle_add(self.refreshLibrary(self.cfgWindow, name, path, True).next)


    def renameLibrary(self, oldName, newName):
        """ Rename a library """
        import shutil

        self.libraries[newName] = self.libraries[oldName]
        del self.libraries[oldName]

        oldPath = os.path.join(ROOT_PATH, oldName)
        newPath = os.path.join(ROOT_PATH, newName)
        shutil.move(oldPath, newPath)

        # Rename tree states as well
        self.renameTreeStates(oldName, newName)

        modules.postMsg(consts.MSG_CMD_EXPLORER_RENAME, {'modName': MOD_L10N, 'expName': oldName, 'newExpName': newName})


    def onRenameLibrary(self, btn):
        """ Let the user rename a library """
        from gui.selectPath import SelectPath

        name         = self.cfgList.getSelectedRows()[0][0]
        forbidden    = [libName for libName in self.libraries if libName != name]
        pathSelector = SelectPath(MOD_L10N, self.cfgWindow, forbidden, ['/'])

        pathSelector.setPathSelectionEnabled(False)
        result = pathSelector.run(name, self.libraries[name][LIB_PATH])

        if result is not None and result[0] != name:
            self.renameLibrary(name, result[0])
            self.fillLibraryList()


    def fillLibraryList(self):
        """ Fill the list of libraries """
        if self.cfgWindow is not None:
            rows = [(name, icons.dirBtnIcon(), '<b>%s</b>\n<small>%s - %u %s</small>' % (htmlEscape(name), htmlEscape(path), nbTracks, htmlEscape(_('tracks'))))
                    for name, (path, nbArtists, nbAlbums, nbTracks) in sorted(self.libraries.iteritems())]
            self.cfgList.replaceContent(rows)


    def removeSelectedLibraries(self, list):
        """ Remove all selected libraries """
        import shutil

        from gui import questionMsgBox

        if list.getSelectedRowsCount() == 1:
            remark   = _('You will be able to recreate this library later on if you wish so.')
            question = _('Remove the selected library?')
        else:
            remark   = _('You will be able to recreate these libraries later on if you wish so.')
            question = _('Remove all selected libraries?')

        if questionMsgBox(self.cfgWindow, question, '%s %s' % (_('Your media files will not be removed.'), remark)) == gtk.RESPONSE_YES:
            for row in list.getSelectedRows():
                # Remove the library from the disk
                libPath = os.path.join(ROOT_PATH, row[0])
                if isdir(libPath):
                    shutil.rmtree(libPath)
                # Remove the corresponding explorer
                modules.postMsg(consts.MSG_CMD_EXPLORER_REMOVE, {'modName': MOD_L10N, 'expName': row[0]})
                del self.libraries[row[0]]
                # Remove tree states
                self.removeTreeStates(row[0])
            # Clean up the listview
            list.removeSelectedRows()


    def onCfgKeyboard(self, list, event):
        """ Remove the selection if possible """
        if gtk.gdk.keyval_name(event.keyval) == 'Delete':
            self.removeSelectedLibraries(list)


    def onCfgSelectionChanged(self, selection):
        """ The selection has changed, update the status of the buttons """
        self.cfgWindow.getWidget('btn-remove').set_sensitive(selection.count_selected_rows() != 0)
        self.cfgWindow.getWidget('btn-rename').set_sensitive(selection.count_selected_rows() == 1)
        self.cfgWindow.getWidget('btn-refresh').set_sensitive(selection.count_selected_rows() == 1)


    def onHelp(self, btn):
        """ Display a small help message box """
        from gui import help

        helpDlg = help.HelpDlg(MOD_L10N)
        helpDlg.addSection(_('Description'),
                           _('This module organizes your media files by tags instead of using the file structure of your drive. '
                             'Loading tracks is also faster because their tags are already known and do not have to be read again.'))
        helpDlg.addSection(_('Usage'),
                           _('When you add a new library, you have to give the full path to the root directory of that library. '
                             'Then, all directories under this root path are recursively scanned for media files whose tags are read '
                             'and stored in a database.') + '\n\n' + _('Upon refreshing a library, the file structure under the root '
                             'directory and all media files are scanned for changes, to update the database accordingly.'))
        helpDlg.show(self.cfgWindow)
