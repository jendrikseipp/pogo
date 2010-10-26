# -*- coding: utf-8 -*-
#
# Authors: Ingelrest François (Francois.Ingelrest@gmail.com)
#          Jendrik Seipp (jendrikseipp@web.de)
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

import re

import gtk, media, modules, os, tools,subprocess

from tools   import consts, prefs, icons
from media   import playlist
from gettext import gettext as _
from os.path import isdir, isfile
from gobject import idle_add, TYPE_STRING, TYPE_INT

MOD_INFO = ('File Explorer', 'File Explorer', 'Browse your file system', [], True, False)
MOD_L10N = MOD_INFO[modules.MODINFO_L10N]

# Default preferences
##PREFS_DEFAULT_MEDIA_FOLDERS     = {'Home': consts.dirBaseUsr, 'Root': '/'}    # List of media folders that are used as roots for the file explorer
PREFS_DEFAULT_ADD_BY_FILENAME   = False                                             # True if files should be added to the playlist by their filename
PREFS_DEFAULT_SHOW_HIDDEN_FILES = False                                             # True if hidden files should be shown

MUSIC_DIRS = ['/home/jendrik/Musik']


# The format of a row in the treeview
(
    ROW_PIXBUF,    # Item icon
    ROW_NAME,      # Item name
    ROW_TYPE,      # The type of the item (e.g., directory, file)
    ROW_FULLPATH   # The full path to the item
) = range(4)


# The possible types for a node of the tree
(
    TYPE_DIR,   # A directory
    TYPE_FILE,  # A media file
    TYPE_NONE   # A fake item, used to display a '+' in front of a directory when needed
) = range(3)


class FileExplorer(modules.Module):
    """ This explorer lets the user browse the disk from a given root directory (e.g., ~/, /) """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_APP_QUIT:         self.onAppQuit,
                        consts.MSG_EVT_APP_STARTED:      self.onAppStarted,
                        consts.MSG_EVT_SEARCH_END:       self.onSearchEnd,
                        consts.MSG_EVT_SEARCH_RESET:     self.onSearchReset,
                   }

        modules.Module.__init__(self, handlers)


    def createTree(self):
        """ Create the tree used to display the file system """
        from gui import extTreeview

        columns = (('',   [(gtk.CellRendererPixbuf(), gtk.gdk.Pixbuf), (gtk.CellRendererText(), TYPE_STRING)], True),
                   (None, [(None, TYPE_INT)],                                                                  False),
                   (None, [(None, TYPE_STRING)],                                                               False))

        self.tree = extTreeview.ExtTreeView(columns, True)

        self.scrolled.add(self.tree)
        self.tree.setDNDSources([consts.DND_TARGETS[consts.DND_POGO_URI]])
        self.tree.connect('drag-data-get', self.onDragDataGet)
        self.tree.connect('key-press-event', self.onKeyPressed)
        self.tree.connect('exttreeview-button-pressed', self.onMouseButton)
        self.tree.connect('exttreeview-row-collapsed', self.onRowCollapsed)
        self.tree.connect('exttreeview-row-expanded', self.onRowExpanded)


    def getTreeDump(self, path=None):
        """ Recursively dump the given tree starting at path (None for the root of the tree) """
        list = []

        for child in self.tree.iterChildren(path):
            row = self.tree.getRow(child)

            if self.tree.getNbChildren(child) == 0: grandChildren = None
            elif self.tree.row_expanded(child):     grandChildren = self.getTreeDump(child)
            else:                                   grandChildren = []

            list.append([(row[ROW_NAME], row[ROW_TYPE], row[ROW_FULLPATH]), grandChildren])

        return list


    def restoreTreeDump(self, dump, parent=None):
        """ Recursively restore the dump under the given parent (None for the root of the tree) """
        for item in dump:
            (name, type, path) = item[0]

            if type == TYPE_FILE:
                self.tree.appendRow((icons.mediaFileMenuIcon(), name, TYPE_FILE, path), parent)
            else:
                newNode = self.tree.appendRow((icons.dirMenuIcon(), name, TYPE_DIR, path), parent)

                if item[1] is not None:
                    fakeChild = self.tree.appendRow((icons.dirMenuIcon(), '', TYPE_NONE, ''), newNode)

                    if len(item[1]) != 0:
                        # We must expand the row before adding the real children, but this works only if there is already at least one child
                        self.tree.expandRow(newNode)
                        self.restoreTreeDump(item[1], newNode)
                        self.tree.removeRow(fakeChild)


    def saveTreeState(self):
        """ Return a dictionary representing the current state of the tree """
        self.treeState = {
                    'tree-state':     self.getTreeDump(),
                    'selected-paths': self.tree.getSelectedPaths(),
                    'vscrollbar-pos': self.scrolled.get_vscrollbar().get_value(),
                    'hscrollbar-pos': self.scrolled.get_hscrollbar().get_value(),
                    }


    def sortKey(self, row):
        """ Key function used to compare two rows of the tree """
        return row[ROW_NAME].lower()


    def play(self, replace, path=None):
        """
            Replace/extend the tracklist
            If 'path' is None, use the current selection
        """
        ## never replace
        replace = False

        if path is None: tracks = media.getTracks([row[ROW_FULLPATH] for row in self.tree.getSelectedRows()], self.addByFilename)
        else:            tracks = media.getTracks([self.tree.getRow(path)[ROW_FULLPATH]], self.addByFilename)

        if replace: modules.postMsg(consts.MSG_CMD_TRACKLIST_SET, {'tracks': tracks, 'playNow': True})
        else:       modules.postMsg(consts.MSG_CMD_TRACKLIST_ADD, {'tracks': tracks, 'playNow': False})


    # --== Tree management ==--


    def startLoading(self, row):
        """ Tell the user that the contents of row is being loaded """
        name = self.tree.getItem(row, ROW_NAME)
        self.tree.setItem(row, ROW_NAME, '%s  <span size="smaller" foreground="#909090">%s</span>' % (name, _('loading...')))


    def stopLoading(self, row):
        """ Tell the user that the contents of row has been loaded"""
        name  = self.tree.getItem(row, ROW_NAME)
        index = name.find('<span')

        if index != -1:
            self.tree.setItem(row, ROW_NAME, name[:index-2])


    def getDirContents(self, directory):
        """ Return a tuple of sorted rows (directories, playlists, mediaFiles) for the given directory """
        playlists   = []
        mediaFiles  = []
        directories = []

        for (file, path) in tools.listDir(directory):
            file = unicode(file, errors='replace')

            # Make directory names prettier
            junk = ['_']
            pretty_name = file
            for item in junk:
                pretty_name = pretty_name.replace(item, ' ')

            if isdir(path):
                directories.append((icons.dirMenuIcon(), tools.htmlEscape(pretty_name), TYPE_DIR, path))
            elif isfile(path):
                if media.isSupported(file):
                    mediaFiles.append((icons.mediaFileMenuIcon(), tools.htmlEscape(pretty_name), TYPE_FILE, path))
                ##elif playlist.isSupported(file):
                ##    playlists.append((icons.mediaFileMenuIcon(), tools.htmlEscape(unicode(file, errors='replace')), TYPE_FILE, path))

        playlists.sort(key=self.sortKey)
        mediaFiles.sort(key=self.sortKey)
        directories.sort(key=self.sortKey)

        return (directories, playlists, mediaFiles)


    def exploreDir(self, parent, directory, fakeChild=None):
        """
            List the contents of the given directory and append it to the tree as a child of parent
            If fakeChild is not None, remove it when the real contents has been loaded
        """
        directories, playlists, mediaFiles = self.getDirContents(directory)

        self.tree.appendRows(directories, parent)
        self.tree.appendRows(playlists,   parent)
        self.tree.appendRows(mediaFiles,  parent)

        if fakeChild is not None:
            self.tree.removeRow(fakeChild)

        idle_add(self.updateDirNodes(parent).next)


    def updateDirNodes(self, parent):
        """ This generator updates the directory nodes, based on whether they should be expandable """
        for child in self.tree.iterChildren(parent):
            # Only directories need to be updated and since they all come first, we can stop as soon as we find something else
            if self.tree.getItem(child, ROW_TYPE) != TYPE_DIR:
                break

            # Make sure it's readable
            directory  = self.tree.getItem(child, ROW_FULLPATH)
            hasContent = False
            if os.access(directory, os.R_OK | os.X_OK):
                for (file, path) in tools.listDir(directory):
                    if isdir(path) or (isfile(path) and (media.isSupported(file) or playlist.isSupported(file))):
                        hasContent = True
                        break

            # Append/remove children if needed
            if hasContent and self.tree.getNbChildren(child) == 0:
                self.tree.appendRow((icons.dirMenuIcon(), '', TYPE_NONE, ''), child)
            elif not hasContent and self.tree.getNbChildren(child) > 0:
                self.tree.removeAllChildren(child)

            yield True

        if parent is not None:
            self.stopLoading(parent)

        yield False


    def refresh(self, treePath=None):
        """ Refresh the tree, starting from treePath """
        if treePath is None:
            # Update all paths
            for child in self.tree.iterChildren(None):
                if self.tree.row_expanded(child):
                    idle_add(self.refresh, child)
            return

        directory = self.tree.getItem(treePath, ROW_FULLPATH)

        directories, playlists, mediaFiles = self.getDirContents(directory)

        disk                   = directories + playlists + mediaFiles
        diskIndex              = 0
        childIndex             = 0
        childLeftIntentionally = False

        while diskIndex < len(disk):
            rowPath = self.tree.getChild(treePath, childIndex)

            # Did we reach the end of the tree?
            if rowPath is None:
                break

            file      = disk[diskIndex]
            cmpResult = cmp(self.sortKey(self.tree.getRow(rowPath)), self.sortKey(file))

            if cmpResult < 0:
                # We can't remove the only child left, to prevent the node from being closed automatically
                if self.tree.getNbChildren(treePath) == 1:
                    childLeftIntentionally = True
                    break

                self.tree.removeRow(rowPath)
            else:
                if cmpResult > 0:
                    self.tree.insertRowBefore(file, treePath, rowPath)
                diskIndex  += 1
                childIndex += 1

        # If there are tree rows left, all the corresponding files are no longer there
        if not childLeftIntentionally:
            while childIndex < self.tree.getNbChildren(treePath):
                self.tree.removeRow(self.tree.getChild(treePath, childIndex))

        # Disk files left?
        while diskIndex < len(disk):
            self.tree.appendRow(disk[diskIndex], treePath)
            diskIndex += 1

        # Deprecated child left? (must be done after the addition of left disk files)
        if childLeftIntentionally:
            self.tree.removeRow(self.tree.getChild(treePath, 0))

        # Update nodes' appearance
        if len(directories) != 0:
            idle_add(self.updateDirNodes(treePath).next)

        # Recursively refresh expanded rows
        for child in self.tree.iterChildren(treePath):
            if self.tree.row_expanded(child):
                idle_add(self.refresh, child)

    def showFolder(self, folderPath):
        """ Show containing folder in default file browser """
        if os.name == 'mac':
            subprocess.call(('open', folderPath))
        elif os.name == 'nt':
            subprocess.call(('start', folderPath))
        elif os.name == 'posix':
            subprocess.call(('xdg-open', folderPath))
    # --== GTK handlers ==--


    def onMouseButton(self, tree, event, path):
        """ A mouse button has been pressed """
        if event.button == 3:
            self.onShowPopupMenu(tree, event.button, event.time, path)
        elif path is not None:
            if event.button == 2:
                self.play(False, path)
            elif event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                if   tree.getItem(path, ROW_PIXBUF) != icons.dirMenuIcon(): self.play(True)
                elif tree.row_expanded(path):                               tree.collapse_row(path)
                else:                                                       tree.expand_row(path, False)


    def onShowPopupMenu(self, tree, button, time, path):
        """ Show a popup menu """
        popup = gtk.Menu()

        # Play selection
        play = gtk.ImageMenuItem(gtk.STOCK_MEDIA_PLAY)
        play.set_label(_('Append'))
        popup.append(play)

        if path is None:
            play.set_sensitive(False)
        else:
            play.connect('activate', lambda widget: self.play(True))

        popup.append(gtk.SeparatorMenuItem())

        # Refresh the view
        refresh = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        refresh.connect('activate', lambda widget: self.refresh())
        popup.append(refresh)

        popup.append(gtk.SeparatorMenuItem())

        #open containing folder
        showFolder = gtk.ImageMenuItem(gtk.STOCK_OPEN)
        showFolder.set_label(_('Open containing folder'))
        folderPaths = [row[ROW_FULLPATH] for row in self.tree.getSelectedRows()]
        folderPath = os.path.dirname(folderPaths[0])
        showFolder.connect('activate', lambda widget: self.showFolder(folderPath))
        popup.append(showFolder)

        popup.show_all()
        popup.popup(None, None, None, button, time)


    def onKeyPressed(self, tree, event):
        """ A key has been pressed """
        keyname = gtk.gdk.keyval_name(event.keyval)

        if keyname == 'F5':       self.refresh()
        elif keyname == 'plus':   tree.expandRows()
        elif keyname == 'Left':   tree.collapseRows()
        elif keyname == 'Right':  tree.expandRows()
        elif keyname == 'minus':  tree.collapseRows()
        elif keyname == 'space':  tree.switchRows()
        elif keyname == 'Return': self.play(True)


    def onRowExpanded(self, tree, path):
        """ Replace the fake child by the real children """
        self.startLoading(path)
        idle_add(self.exploreDir, path, tree.getItem(path, ROW_FULLPATH), tree.getChild(path, 0))


    def onRowCollapsed(self, tree, path):
        """ Replace all children by a fake child """
        tree.removeAllChildren(path)
        tree.appendRow((icons.dirMenuIcon(), '', TYPE_NONE, ''), path)


    def onDragDataGet(self, tree, context, selection, info, time):
        """ Provide information about the data being dragged """
        import urllib
        selection.set('text/uri-list', 8, ' '.join([urllib.pathname2url(file) for file in [row[ROW_FULLPATH] for row in tree.getSelectedRows()]]))


    def add_dir(self, path):
        '''
        Add a directory with one fake child to the tree
        '''
        name = tools.dirname(path)
        name = tools.htmlEscape(unicode(name, errors='replace'))
        parent = self.tree.appendRow((icons.dirMenuIcon(), name, TYPE_DIR, path), None)
        fakeChild = self.tree.appendRow((icons.dirMenuIcon(), '', TYPE_NONE, ''), parent)


    def _is_separator(self, model, iter):
        return model[iter][ROW_NAME] is None


    def restore_tree(self):
        self.tree.handler_block_by_func(self.onRowExpanded)
        self.restoreTreeDump(self.treeState['tree-state'])
        self.tree.handler_unblock_by_func(self.onRowExpanded)
        idle_add(self.scrolled.get_vscrollbar().set_value, self.treeState['vscrollbar-pos'])
        idle_add(self.scrolled.get_hscrollbar().set_value, self.treeState['hscrollbar-pos'])
        idle_add(self.tree.selectPaths, self.treeState['selected-paths'])
        idle_add(self.refresh)


    def populate_tree(self):
        '''
        Bookmarks code from Quod Libet
        '''
        assert self.tree is None
        self.createTree()
        #self.tree.set_row_separator_func(lambda model, iter: model[iter][ROW_NAME] is None)
        self.tree.set_row_separator_func(self._is_separator)

        # Restore the tree if we have any to restore, else build new one
        if self.treeState:
            self.restore_tree()
            return

        folders = ['/', consts.dirBaseUsr]

        def add_path(path, prepend=False):
            if not os.path.isdir(path) or path in folders:
                return
            if prepend:
                folders.insert(0, path)
            else:
                folders.append(path)

        # Read XDG music directory
        xdg_file = os.path.join(consts.dirBaseUsr, '.config', 'user-dirs.dirs')
        if os.path.exists(xdg_file):
            with open(xdg_file) as f:
                import re
                folder_regex = re.compile(r'XDG_MUSIC_DIR\=\"\$HOME/(.+)\"')

                content = f.read()
                match = folder_regex.search(content)
                if match:
                    dirname = match.group(1)
                    path = os.path.join(consts.dirBaseUsr, dirname)
                    folders.append(None)
                    add_path(path, prepend=False)
                else:
                    # Try other music folders
                    names = ['Music', 'Albums', _('Music'), _('Albums')]
                    for name in names:
                        for case in [name, name.lower()]:
                            music_folder = os.path.join(consts.dirBaseUsr, name)
                            if os.path.isdir(music_folder):
                                add_path(music_folder)


        # Read in the GTK bookmarks list; gjc says this is the right way
        # import urlparse, urllib2
        #bookmarks_file = os.path.join(consts.dirBaseUsr, ".gtk-bookmarks")
        #if os.path.exists(bookmarks_file):
        #    try:
        #        with open(bookmarks_file) as f:
        #            folders.append(None)
        #            for line in f.readlines():
        #                folder_url = line.split()[0]
        #                path = urlparse.urlsplit(folder_url)[2]
        #                # "My%20folder" -> "My folder"
        #                path = urllib2.unquote(path)
        #                add_path(path)
        #    except EnvironmentError:
        #        pass

        #def is_folder(filename):
        #    return filename is None or os.path.isdir(filename)
        #folders = filter(is_folder, folders)
        #if folders[-1] is None:
        #    folders.pop()

        for path in folders:
            if path is None:
                # Separator
                self.tree.appendRow((icons.nullMenuIcon(), None, TYPE_NONE, None), None)
            else:
                self.add_dir(path)


   # --== Message handlers ==--


    def onAppStarted(self):
        """ The module has been loaded """
        self.tree            = None
        self.cfgWin          = None
        self.scrolled        = gtk.ScrolledWindow()
        self.treeState       = prefs.get(__name__, 'saved-states', None)
        self.addByFilename   = PREFS_DEFAULT_ADD_BY_FILENAME

        self.scrolled.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled.show()

        ##
        left_vbox = prefs.getWidgetsTree().get_widget('vbox3')
        left_vbox.pack_start(self.scrolled)

        self.displaying_results = False
        self.populate_tree()

        self.tree.connect('drag-begin', self.onDragBegin)


    def onAppQuit(self):
        """ The module is going to be unloaded """
        if not self.displaying_results:
            self.saveTreeState()
            prefs.set(__name__, 'saved-states', self.treeState)


    def onSearchEnd(self, results, query):
        if not self.displaying_results:
            self.saveTreeState()

        self.tree.clear()

        last_dir = ''
        last_dir_iter = None

        dirs = []
        files = []
        for path in results:
            # Check if this is only a subpath of a directory already handled
            is_subpath = False
            for dir in dirs:
                if path.startswith(dir):
                    is_subpath = True
                    break

            if not is_subpath:
                if os.path.isdir(path):
                    dirs.append(path)
                elif media.isSupported(path):
                    files.append(path)

        def same_case_bold(match):
            return '<b>%s</b>' % match.group(0)

        regexes = [re.compile(part, re.IGNORECASE) for part in query.split()]

        def get_nodename(path):
            name = path
            for music_dir in MUSIC_DIRS:
                name = name.replace(music_dir, '')
            name = name.strip('/')
            name = tools.htmlEscape(name)
            for regex in regexes:
                name = regex.sub(same_case_bold, name)
            return name

        for path in dirs:
            name = get_nodename(path)
            new_node = self.tree.appendRow((icons.dirMenuIcon(), name, TYPE_DIR, path), None)
            fakeChild = self.tree.appendRow((icons.dirMenuIcon(), '', TYPE_NONE, ''), new_node)

        for file in files:
            filename = get_nodename(file)
            self.tree.appendRow((icons.mediaFileMenuIcon(), filename, TYPE_FILE, file), None)

        self.displaying_results = True


    def onSearchReset(self):
        if self.displaying_results:
            self.tree.clear()
            self.restore_tree()
            self.displaying_results = False


    # --== GTK Handlers ==--

    def onDragBegin(self, tree, context):
        """
        A drag'n'drop operation has begun
        Copy the selected paths to the tracktree to decide on correct drop positions
        """
        paths = [row[ROW_FULLPATH] for row in tree.getSelectedRows()]
        modules.postMsg(consts.MSG_CMD_FILE_EXPLORER_DRAG_BEGIN, {'paths': paths})
        #idle_add(media.getTracks, paths)

        # Preload the tracks to speedup their addition to the playlist
        import threading
        crawler = threading.Thread(target=media.preloadTracks, args=(paths,))
        crawler.start()

        #from multiprocessing import Process
        #p = Process(target=media.getTracks, args=(paths,))
        #p.start()

        #from multiprocessing import Pool
        #pool = Pool(processes=4)              # start 4 worker processes
        #result = pool.map_async(media.getTracks, [[path] for path in paths])

